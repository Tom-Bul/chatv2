#!/usr/bin/env python3
import sys
import os
from pathlib import Path
import pytest
import time
import cProfile
import pstats
import logging
import argparse
import asyncio
from datetime import datetime
import json
import psutil
import shutil

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# Set up logging
logging.basicConfig(
    filename='test_run.log',
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configure pytest
def pytest_configure(config):
    """Configure pytest."""
    config.addinivalue_line(
        "markers",
        "asyncio: mark test as requiring asyncio"
    )

class TestRunner:
    def __init__(self, args):
        self.args = args
        self.results_dir = project_root / "test_results"
        self.results_dir.mkdir(exist_ok=True)
        
        # Create results for this run
        self.run_dir = self.results_dir / datetime.now().strftime("%Y%m%d_%H%M%S")
        if self.run_dir.exists():
            shutil.rmtree(self.run_dir)
        self.run_dir.mkdir()
        
        # Performance data
        self.performance_data = {
            "test_times": {},
            "memory_usage": {},
            "cpu_usage": {},
            "ai_calls": {},
            "errors": []
        }
    
    def setup_environment(self):
        """Set up test environment."""
        # Create temporary directories
        (self.run_dir / "temp").mkdir(exist_ok=True)
        (self.run_dir / "logs").mkdir(exist_ok=True)
        
        # Set environment variables
        os.environ["TEST_MODE"] = "1"
        os.environ["TEST_RUN_DIR"] = str(self.run_dir)
        
        # Disable Qt tests by default
        os.environ["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
        
        logger.info("Test environment set up in %s", self.run_dir)
    
    def run_tests(self):
        """Run the test suite."""
        logger.info("Starting test run")
        
        # Set up test environment
        self.setup_environment()
        
        # Build pytest arguments
        pytest_args = [
            f"--basetemp={self.run_dir/'temp'}",
            "-p", "no:qt",  # Disable Qt plugin
            "--ignore=tests/test_game_window.py"  # Ignore UI tests
        ]
        
        if self.args.monitor:
            pytest_args.extend(["-v", "--log-cli-level=DEBUG"])
        
        if self.args.profile:
            profiler = cProfile.Profile()
            profiler.enable()
        
        # Run tests
        try:
            result = pytest.main(pytest_args)
            logger.info("Test run completed with exit code %d", result)
            
            if self.args.profile:
                profiler.disable()
                stats = pstats.Stats(profiler, stream=sys.stdout)
                stats.sort_stats('cumulative')
                stats.print_stats()
                
        except Exception as e:
            logger.error("Error running tests: %s", e)
            raise
    
    def monitor_performance(self):
        """Monitor system performance during tests."""
        process = psutil.Process()
        
        while True:
            try:
                # Get memory usage
                memory_info = process.memory_info()
                self.performance_data["memory_usage"][time.time()] = {
                    "rss": memory_info.rss,
                    "vms": memory_info.vms
                }
                
                # Get CPU usage
                cpu_percent = process.cpu_percent()
                self.performance_data["cpu_usage"][time.time()] = cpu_percent
                
                time.sleep(1)  # Sample every second
                
            except psutil.NoSuchProcess:
                break  # Process ended
    
    def generate_report(self):
        """Generate test run report."""
        report = {
            "timestamp": datetime.now().isoformat(),
            "args": vars(self.args),
            "performance": self.performance_data,
            "system_info": {
                "python_version": sys.version,
                "platform": sys.platform,
                "cpu_count": psutil.cpu_count(),
                "memory_total": psutil.virtual_memory().total
            }
        }
        
        # Save report
        with open(self.run_dir / "report.json", 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info("Test report generated")
    
    def cleanup(self):
        """Clean up test results directory."""
        if self.run_dir.exists():
            shutil.rmtree(self.run_dir)
        
        logger.info("Test environment cleaned up")
    
    async def run(self):
        """Run the complete test suite with monitoring."""
        try:
            # Set up
            self.setup_environment()
            
            # Start performance monitoring in background
            if self.args.monitor:
                import threading
                monitor_thread = threading.Thread(
                    target=self.monitor_performance,
                    daemon=True
                )
                monitor_thread.start()
            
            # Run tests
            self.run_tests()
            
            # Generate report
            self.generate_report()
            
        finally:
            # Clean up
            self.cleanup()

def main():
    parser = argparse.ArgumentParser(description="Run test suite")
    parser.add_argument("--monitor", action="store_true", help="Enable monitoring")
    parser.add_argument("--profile", action="store_true", help="Enable profiling")
    parser.add_argument("--no-ui", action="store_true", help="Skip UI tests")
    parser.add_argument("--keep-temp", action="store_true", help="Keep temporary files")
    args = parser.parse_args()
    
    runner = TestRunner(args)
    asyncio.run(runner.run())

if __name__ == "__main__":
    main() 