"""
Performance tests for memory usage and processing speed with full character database.
"""

import unittest
import tempfile
import shutil
import os
import time
import gc
from pathlib import Path
from PIL import Image

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

from card_generator.data_loader import CSVDataLoader
from card_generator.image_processor import ImageProcessor
from card_generator.card_designer import CardDesigner
from card_generator.print_layout import PrintLayoutManager
from card_generator.output_manager import OutputManager
from card_generator.config import CardConfig, PrintConfig, OutputConfig


class TestPerformance(unittest.TestCase):
    """Performance tests for memory usage and processing speed."""
    
    def setUp(self):
        """Set up test environment."""
        self.test_dir = tempfile.mkdtemp()
        self.images_dir = os.path.join(self.test_dir, 'images')
        self.output_dir = os.path.join(self.test_dir, 'output')
        os.makedirs(self.images_dir)
        os.makedirs(self.output_dir)
        
        # Use real CSV file if available
        self.csv_path = 'steal_a_brainrot_complete_database.csv'
        if not os.path.exists(self.csv_path):
            self.skipTest("CSV file not found - skipping performance tests")
        
        # Initialize components
        self.data_loader = CSVDataLoader()
        self.image_processor = ImageProcessor()
        self.card_designer = CardDesigner(CardConfig())
        self.print_layout = PrintLayoutManager(PrintConfig())
        self.output_manager = OutputManager(OutputConfig(
            individual_cards_dir=os.path.join(self.output_dir, 'cards'),
            print_sheets_dir=os.path.join(self.output_dir, 'sheets')
        ))
        
        # Performance thresholds
        self.MAX_MEMORY_MB = 500  # Maximum memory usage in MB
        self.MAX_LOAD_TIME_SECONDS = 5.0  # Maximum time to load all characters
        self.MAX_CARD_GENERATION_TIME_MS = 100  # Maximum time per card in milliseconds
    
    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.test_dir)
        gc.collect()  # Force garbage collection
    
    def get_memory_usage_mb(self):
        """Get current memory usage in MB."""
        if not PSUTIL_AVAILABLE:
            return 0.0  # Return 0 if psutil is not available
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / 1024 / 1024
    
    @unittest.skipUnless(PSUTIL_AVAILABLE, "psutil not available")
    def test_csv_loading_performance(self):
        """Test CSV loading performance with full database."""
        # Measure memory before loading
        memory_before = self.get_memory_usage_mb()
        
        # Measure loading time
        start_time = time.time()
        characters = self.data_loader.load_characters(
            csv_path=self.csv_path,
            images_dir='images'  # Use real images directory
        )
        load_time = time.time() - start_time
        
        # Measure memory after loading
        memory_after = self.get_memory_usage_mb()
        memory_used = memory_after - memory_before
        
        # Performance assertions
        self.assertLess(load_time, self.MAX_LOAD_TIME_SECONDS,
                       f"CSV loading took {load_time:.2f}s, expected < {self.MAX_LOAD_TIME_SECONDS}s")
        
        self.assertLess(memory_used, self.MAX_MEMORY_MB,
                       f"CSV loading used {memory_used:.2f}MB, expected < {self.MAX_MEMORY_MB}MB")
        
        # Verify we loaded a reasonable number of characters
        self.assertGreater(len(characters), 50, "Expected to load more than 50 characters")
        
        print(f"CSV Loading Performance:")
        print(f"  Characters loaded: {len(characters)}")
        print(f"  Load time: {load_time:.3f}s")
        print(f"  Memory used: {memory_used:.2f}MB")
        print(f"  Characters per second: {len(characters)/load_time:.1f}")
    
    def test_image_processing_performance(self):
        """Test image processing performance."""
        # Create test images of various sizes
        test_sizes = [(100, 100), (500, 500), (1000, 1000), (2000, 2000)]
        test_images = []
        
        for i, size in enumerate(test_sizes):
            img = Image.new('RGB', size, (255, 0, 0))
            path = os.path.join(self.images_dir, f'test_{i}.png')
            img.save(path)
            test_images.append(path)
        
        # Measure processing time for each image size
        processing_times = []
        memory_before = self.get_memory_usage_mb()
        
        for i, image_path in enumerate(test_images):
            start_time = time.time()
            
            # Load and process image
            image = self.image_processor.load_image(image_path)
            if image is not None:  # Only process if image loaded successfully
                processed = self.image_processor.resize_and_crop(image, (400, 600))
                
                processing_time = (time.time() - start_time) * 1000  # Convert to milliseconds
                processing_times.append(processing_time)
                
                # Verify processed image
                if processed is not None:
                    self.assertEqual(processed.size, (400, 600))
                
                print(f"Image {test_sizes[i]} processed in {processing_time:.2f}ms")
            else:
                print(f"Image {test_sizes[i]} skipped (too small or invalid)")
        
        memory_after = self.get_memory_usage_mb()
        memory_used = memory_after - memory_before
        
        # Performance assertions (only if we have processing times)
        if processing_times:
            max_processing_time = max(processing_times)
            self.assertLess(max_processing_time, self.MAX_CARD_GENERATION_TIME_MS * 2,
                           f"Image processing took {max_processing_time:.2f}ms, expected < {self.MAX_CARD_GENERATION_TIME_MS * 2}ms")
        else:
            self.skipTest("No images were processed successfully")
        
        print(f"Image Processing Performance:")
        if processing_times:
            print(f"  Max processing time: {max(processing_times):.2f}ms")
        print(f"  Memory used: {memory_used:.2f}MB")
    
    def test_card_generation_performance(self):
        """Test card generation performance with multiple characters."""
        # Load a subset of characters for testing
        characters = self.data_loader.load_characters(
            csv_path=self.csv_path,
            images_dir='images'
        )
        
        # Test with first 20 characters
        test_characters = characters[:20]
        
        memory_before = self.get_memory_usage_mb()
        generation_times = []
        
        for character in test_characters:
            # Create test image
            test_image = Image.new('RGB', (400, 400), (0, 255, 0))
            
            # Measure card generation time
            start_time = time.time()
            card = self.card_designer.create_card(character, test_image)
            generation_time = (time.time() - start_time) * 1000  # Convert to milliseconds
            generation_times.append(generation_time)
            
            # Verify card was created
            self.assertIsNotNone(card)
            self.assertEqual(card.size, (1748, 2480))
        
        memory_after = self.get_memory_usage_mb()
        memory_used = memory_after - memory_before
        
        # Performance metrics
        avg_generation_time = sum(generation_times) / len(generation_times)
        max_generation_time = max(generation_times)
        total_time = sum(generation_times) / 1000  # Convert to seconds
        
        # Performance assertions
        self.assertLess(avg_generation_time, self.MAX_CARD_GENERATION_TIME_MS,
                       f"Average card generation took {avg_generation_time:.2f}ms, expected < {self.MAX_CARD_GENERATION_TIME_MS}ms")
        
        self.assertLess(memory_used, self.MAX_MEMORY_MB,
                       f"Card generation used {memory_used:.2f}MB, expected < {self.MAX_MEMORY_MB}MB")
        
        print(f"Card Generation Performance:")
        print(f"  Cards generated: {len(test_characters)}")
        print(f"  Average time per card: {avg_generation_time:.2f}ms")
        print(f"  Max time per card: {max_generation_time:.2f}ms")
        print(f"  Total time: {total_time:.2f}s")
        print(f"  Memory used: {memory_used:.2f}MB")
        print(f"  Cards per second: {len(test_characters)/total_time:.1f}")
    
    def test_batch_processing_performance(self):
        """Test performance of processing large batches of characters."""
        # Load all characters
        characters = self.data_loader.load_characters(
            csv_path=self.csv_path,
            images_dir='images'
        )
        
        # Test with larger batch (50 characters or all if fewer)
        batch_size = min(50, len(characters))
        test_batch = characters[:batch_size]
        
        memory_before = self.get_memory_usage_mb()
        start_time = time.time()
        
        # Process entire batch
        generated_cards = []
        for character in test_batch:
            # Use placeholder for consistent testing
            image = self.image_processor.create_placeholder(
                (400, 400), character.name, character.tier
            )
            card = self.card_designer.create_card(character, image)
            generated_cards.append(card)
        
        # Create print sheets
        print_sheets = self.print_layout.create_print_sheets(generated_cards)
        
        total_time = time.time() - start_time
        memory_after = self.get_memory_usage_mb()
        memory_used = memory_after - memory_before
        
        # Performance metrics
        cards_per_second = len(test_batch) / total_time
        memory_per_card = memory_used / len(test_batch)
        
        # Performance assertions
        self.assertLess(total_time, batch_size * 0.2,  # 200ms per card maximum
                       f"Batch processing took {total_time:.2f}s for {batch_size} cards")
        
        self.assertLess(memory_used, self.MAX_MEMORY_MB * 2,  # Allow more memory for batch
                       f"Batch processing used {memory_used:.2f}MB")
        
        print(f"Batch Processing Performance:")
        print(f"  Batch size: {batch_size} cards")
        print(f"  Total time: {total_time:.2f}s")
        print(f"  Cards per second: {cards_per_second:.1f}")
        print(f"  Memory used: {memory_used:.2f}MB")
        print(f"  Memory per card: {memory_per_card:.2f}MB")
        print(f"  Print sheets created: {len(print_sheets)}")
    
    @unittest.skipUnless(PSUTIL_AVAILABLE, "psutil not available")
    def test_memory_cleanup(self):
        """Test that memory is properly cleaned up after processing."""
        # Get baseline memory
        gc.collect()
        baseline_memory = self.get_memory_usage_mb()
        
        # Process some characters
        characters = self.data_loader.load_characters(
            csv_path=self.csv_path,
            images_dir='images'
        )
        
        test_characters = characters[:10]
        for character in test_characters:
            image = self.image_processor.create_placeholder(
                (400, 400), character.name, character.tier
            )
            card = self.card_designer.create_card(character, image)
            # Explicitly delete references
            del image, card
        
        # Clean up references
        del characters, test_characters
        gc.collect()
        
        # Check memory after cleanup
        final_memory = self.get_memory_usage_mb()
        memory_increase = final_memory - baseline_memory
        
        # Should not have significant memory increase after cleanup
        self.assertLess(memory_increase, 50,  # Allow 50MB increase
                       f"Memory increased by {memory_increase:.2f}MB after cleanup")
        
        print(f"Memory Cleanup Test:")
        print(f"  Baseline memory: {baseline_memory:.2f}MB")
        print(f"  Final memory: {final_memory:.2f}MB")
        print(f"  Memory increase: {memory_increase:.2f}MB")


if __name__ == '__main__':
    if not PSUTIL_AVAILABLE:
        print("Warning: psutil not available - memory usage tests will be skipped")
        print("Install with: pip install psutil")
    
    unittest.main(verbosity=2)