#!/usr/bin/env python3
"""
Asana Simulation Seed Data Generator

Main entry point for generating realistic Asana seed data.
Generates a SQLite database with all Asana entities.

Usage:
    python src/main.py [options]
    
Options:
    --users NUM         Number of users to generate (default: 5000)
    --history-months N  Months of historical data (default: 6)
    --tasks-per-user N  Average tasks per user (default: 10)
    --seed NUM          Random seed for reproducibility
    --output PATH       Output database path
    --minimal           Generate minimal dataset for testing
    --verbose           Enable verbose logging
"""

import os
import sys
import argparse
import logging
import time
from pathlib import Path
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

from src.utils import Database
from src.generators.methodology_generator import MethodologyBasedGenerator


def setup_logging(verbose: bool = False):
    """Configure logging."""
    level = logging.DEBUG if verbose else logging.INFO
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(message)s',
        datefmt='%H:%M:%S'
    )
    
    # Console handler
    console = logging.StreamHandler()
    console.setLevel(level)
    console.setFormatter(formatter)
    
    # Root logger
    root = logging.getLogger()
    root.setLevel(level)
    root.addHandler(console)
    
    # Reduce noise from other libraries
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Generate realistic Asana simulation data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Generate with default settings (5000 users)
    python src/main.py
    
    # Generate large dataset
    python src/main.py --users 10000 --tasks-per-user 15
    
    # Generate minimal test dataset
    python src/main.py --minimal
    
    # Reproducible generation
    python src/main.py --seed 42
        """
    )
    
    parser.add_argument(
        "--users", "-u",
        type=int,
        default=None,
        help="Number of users to generate (default: from .env or 5000)"
    )
    
    parser.add_argument(
        "--organizations", "-org",
        type=int,
        default=None,
        help="Number of organizations to generate (default: from .env or 3)"
    )
    
    parser.add_argument(
        "--history-months", "-m",
        type=int,
        default=None,
        help="Months of historical data (default: 6)"
    )
    
    parser.add_argument(
        "--tasks-per-user", "-t",
        type=int,
        default=None,
        help="Average tasks per user (default: 10)"
    )
    
    parser.add_argument(
        "--seed", "-s",
        type=int,
        default=None,
        help="Random seed for reproducibility"
    )
    
    parser.add_argument(
        "--output", "-o",
        type=str,
        default=None,
        help="Output database path (default: output/asana_simulation.sqlite)"
    )
    
    parser.add_argument(
        "--minimal",
        action="store_true",
        help="Generate minimal dataset (100 users, 5 tasks/user)"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    
    return parser.parse_args()


def main():
    """Main entry point."""
    # Load environment variables
    load_dotenv()
    
    # Parse arguments
    args = parse_args()
    
    # Setup logging
    setup_logging(args.verbose or os.getenv("VERBOSE", "").lower() == "true")
    logger = logging.getLogger(__name__)
    
    # Print banner
    logger.info("=" * 60)
    logger.info("ASANA SIMULATION SEED DATA GENERATOR")
    logger.info("=" * 60)
    
    # Determine configuration
    if args.minimal:
        num_users = 100
        num_organizations = 2
        tasks_per_user = 5
        history_months = 2
    else:
        num_users = args.users or int(os.getenv("NUM_USERS", 5000))
        num_organizations = args.organizations or int(os.getenv("NUM_ORGANIZATIONS", 3))
        tasks_per_user = args.tasks_per_user or int(os.getenv("TASKS_PER_USER", 10))
        history_months = args.history_months or int(os.getenv("HISTORY_MONTHS", 6))
    
    random_seed = args.seed or (int(os.getenv("RANDOM_SEED")) if os.getenv("RANDOM_SEED") else None)
    
    # Output path
    output_dir = os.getenv("OUTPUT_DIR", "output")
    db_name = os.getenv("DATABASE_NAME", "asana_simulation.sqlite")
    output_path = args.output or os.path.join(output_dir, db_name)
    
    # Get schema path
    script_dir = Path(__file__).parent.parent
    schema_path = script_dir / "schema.sql"
    
    logger.info(f"Configuration:")
    logger.info(f"  Organizations: {num_organizations}")
    logger.info(f"  Users: {num_users:,}")
    logger.info(f"  Tasks per user: {tasks_per_user}")
    logger.info(f"  History months: {history_months}")
    logger.info(f"  Random seed: {random_seed or 'None (random)'}")
    logger.info(f"  Output: {output_path}")
    logger.info("-" * 60)
    
    # Start timing
    start_time = time.time()
    
    # Initialize database
    logger.info("Initializing database...")
    
    # Remove existing database
    if os.path.exists(output_path):
        os.remove(output_path)
        logger.info(f"  Removed existing database")
    
    # Create database and apply schema
    db = Database(output_path)
    db.connect()
    
    if schema_path.exists():
        db.execute_script(str(schema_path))
        logger.info(f"  Applied schema from {schema_path}")
    else:
        logger.error(f"Schema file not found: {schema_path}")
        sys.exit(1)
    
    # Initialize generator (uses methodology-based generation)
    generator = MethodologyBasedGenerator(
        num_users=num_users,
        num_organizations=num_organizations,
        history_months=history_months,
        tasks_per_user=tasks_per_user,
        random_seed=random_seed
    )
    
    # Generate data
    try:
        counts = generator.generate_all(db)
    except Exception as e:
        logger.error(f"Generation failed: {e}")
        import traceback
        traceback.print_exc()
        db.close()
        sys.exit(1)
    
    # Print summary
    elapsed = time.time() - start_time
    
    logger.info("")
    logger.info("=" * 60)
    logger.info("GENERATION COMPLETE")
    logger.info("=" * 60)
    
    total_rows = 0
    for table, count in sorted(counts.items()):
        logger.info(f"  {table}: {count:,} rows")
        total_rows += count
    
    logger.info("-" * 60)
    logger.info(f"  TOTAL: {total_rows:,} rows")
    logger.info(f"  TIME: {elapsed:.1f} seconds")
    logger.info(f"  OUTPUT: {output_path}")
    logger.info("=" * 60)
    
    # Close database
    db.close()
    
    # Print file size
    file_size = os.path.getsize(output_path) / (1024 * 1024)
    logger.info(f"Database size: {file_size:.1f} MB")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())