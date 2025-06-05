import os
import sys
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('workflow.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def run_collection():
    """Run the data collection script."""
    logger.info("Starting data collection...")
    try:
        from src.collect.scrape import main as collect_main
        collect_main()
        logger.info("Data collection completed successfully")
        return True
    except Exception as e:
        logger.error(f"Error during data collection: {str(e)}")
        return False

def run_preparation():
    """Run the data preparation script."""
    logger.info("Starting data preparation...")
    try:
        from src.prepare.convert import main as prepare_main
        prepare_main()
        logger.info("Data preparation completed successfully")
        return True
    except Exception as e:
        logger.error(f"Error during data preparation: {str(e)}")
        return False

def run_dashboard_generation():
    """Run the dashboard generation script."""
    logger.info("Starting dashboard generation...")
    try:
        from src.access.generate_dashboard import main as dashboard_main
        dashboard_main()
        logger.info("Dashboard generation completed successfully")
        return True
    except Exception as e:
        logger.error(f"Error during dashboard generation: {str(e)}")
        return False

def main():
    """Run the complete workflow."""
    start_time = datetime.now()
    logger.info(f"Starting workflow at {start_time}")
    
    # Skip collection since papers are already processed
    logger.info("Skipping data collection as papers are already processed")
    
    # Run preparation
    if not run_preparation():
        logger.error("Workflow failed during preparation phase")
        return
    
    # Generate dashboard
    if not run_dashboard_generation():
        logger.error("Workflow failed during dashboard generation phase")
        return
    
    end_time = datetime.now()
    duration = end_time - start_time
    logger.info(f"Workflow completed successfully in {duration}")

if __name__ == "__main__":
    main() 