"""Main entry point for training data generation."""
import asyncio
import argparse
import logging
import sys
from pathlib import Path

from src.config import Config
from src.pipeline import TrainingDataPipeline
from src.export import TrainingDataExporter
from src.storage.db import TrainingDataDB
from src.web_server import run_web_server

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def generate_data(target_count: int, config: Config, enable_web: bool = True, check_existing: bool = True):
    """Generate training data."""
    # Check if target is already reached
    if check_existing:
        db_check = TrainingDataDB(config.db_path)
        stats = db_check.get_stats()
        if stats["valid"] >= target_count:
            logger.info(f"Target already reached: {stats['valid']}/{target_count} valid examples")
            logger.info("Skipping generation. Use --force to regenerate.")
            # Still start web server if enabled
            if enable_web:
                await db_check.start()
                web_server = run_web_server(config, db_check)
                logger.info("Web UI available at http://localhost:5000")
                try:
                    while True:
                        await asyncio.sleep(60)
                except KeyboardInterrupt:
                    await db_check.stop()
            return
    
    pipeline = TrainingDataPipeline(config)
    web_server = None
    
    try:
        await pipeline.initialize()
        
        # Start web server if enabled
        if enable_web:
            web_server = run_web_server(config, pipeline.db, pipeline)
            logger.info("Web UI available at http://localhost:5000")
        
        await pipeline.generate(target_count, web_server)
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.error(f"Pipeline error: {e}", exc_info=True)
    finally:
        await pipeline.cleanup()


async def export_data(config: Config, train_split: float = 0.8, val_split: float = 0.1, test_split: float = 0.1):
    """Export data to training format."""
    db = TrainingDataDB(config.db_path)
    exporter = TrainingDataExporter(db, config.output_dir)
    exporter.export_to_llama_format(train_split, val_split, test_split)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="Generate synthetic training data for Qwen3 fine-tuning")
    
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Generate command
    gen_parser = subparsers.add_parser("generate", help="Generate training data")
    gen_parser.add_argument(
        "--count",
        type=int,
        default=23333,
        help="Target number of valid examples to generate (default: 23333)"
    )
    gen_parser.add_argument(
        "--no-web",
        action="store_true",
        help="Disable web UI (default: enabled)"
    )
    gen_parser.add_argument(
        "--force",
        action="store_true",
        help="Force generation even if target is already reached"
    )
    
    # Export command
    export_parser = subparsers.add_parser("export", help="Export data to training format")
    export_parser.add_argument(
        "--train-split",
        type=float,
        default=0.8,
        help="Training split (default: 0.8)"
    )
    export_parser.add_argument(
        "--val-split",
        type=float,
        default=0.1,
        help="Validation split (default: 0.1)"
    )
    export_parser.add_argument(
        "--test-split",
        type=float,
        default=0.1,
        help="Test split (default: 0.1)"
    )
    
    # Stats command
    stats_parser = subparsers.add_parser("stats", help="Show database statistics")
    
    # Serve command (web server only, no generation)
    serve_parser = subparsers.add_parser("serve", help="Start web server only (no generation)")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    try:
        config = Config.from_env()
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        sys.exit(1)
    
    if args.command == "generate":
        asyncio.run(generate_data(args.count, config, enable_web=not args.no_web, check_existing=not args.force))
    
    elif args.command == "export":
        asyncio.run(export_data(config, args.train_split, args.val_split, args.test_split))
    
    elif args.command == "stats":
        db = TrainingDataDB(config.db_path)
        stats = db.get_stats()
        print(f"Database Statistics:")
        print(f"  Total examples: {stats['total']}")
        print(f"  Valid examples: {stats['valid']}")
        print(f"  Invalid examples: {stats['invalid']}")
        if stats['total'] > 0:
            valid_pct = (stats['valid'] / stats['total']) * 100
            print(f"  Validation rate: {valid_pct:.1f}%")
    
    elif args.command == "serve":
        # Start web server only
        async def serve_web():
            db = TrainingDataDB(config.db_path)
            await db.start()  # Start DB queue worker
            web_server = run_web_server(config, db)
            logger.info("Web server started. Access at http://localhost:5000")
            # Keep running
            try:
                while True:
                    await asyncio.sleep(60)
            except KeyboardInterrupt:
                logger.info("Shutting down web server")
                await db.stop()
        
        asyncio.run(serve_web())


if __name__ == "__main__":
    main()

