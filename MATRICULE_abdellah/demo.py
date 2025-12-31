"""
Demo script for Train OCR Pipeline
Processes video and generates annotated output
"""

import cv2
import argparse
import sys
from pathlib import Path
from integration import TrainDetectionOCRPipeline, DetectionOCRInterface
import config


def process_video_demo(input_video: str, output_video: str):
    """
    Process video and create annotated output
    
    Args:
        input_video: Path to input video file
        output_video: Path to save annotated video
    """
    # Check if input exists
    if not Path(input_video).exists():
        print(f"Error: Input video not found: {input_video}")
        return
    
    # Initialize pipeline
    print("Initializing Train OCR Pipeline...")
    pipeline = TrainDetectionOCRPipeline()
    
    # Process video
    try:
        stats = pipeline.process_video(input_video, output_video)
        
        # Print results
        print("\n" + "="*50)
        print("PROCESSING SUMMARY")
        print("="*50)
        print(f"Processed frames: {stats['processed_frames']}/{stats['total_frames']}")
        print(f"Total detections: {stats['total_detections']}")
        print(f"Unique wagon IDs: {len(stats['unique_wagons'])}")
        print(f"\nDetected wagons:")
        for wagon_id in stats['unique_wagons']:
            print(f"  - {wagon_id}")
        print(f"\nOutput saved to: {output_video}")
        print("="*50)
        
    except Exception as e:
        print(f"Error processing video: {e}")
        import traceback
        traceback.print_exc()


def process_webcam_demo():
    """
    Real-time demo using webcam
    """
    print("Starting webcam demo...")
    print("Press 'q' to quit")
    
    # Initialize pipeline
    pipeline = TrainDetectionOCRPipeline()
    
    # Open webcam
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Cannot open webcam")
        return
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # Process frame
        annotated, ocr_results = pipeline.process_frame(frame)
        
        # Display results
        cv2.imshow('Train OCR Demo', annotated)
        
        # Print detections
        if ocr_results:
            print(f"Detected: {[r['wagon_id'] for r in ocr_results]}")
        
        # Check for quit
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()


def process_image_demo(input_image: str, output_image: str):
    """
    Process single image
    
    Args:
        input_image: Path to input image
        output_image: Path to save annotated image
    """
    if not Path(input_image).exists():
        print(f"Error: Input image not found: {input_image}")
        return
    
    # Load image
    frame = cv2.imread(input_image)
    if frame is None:
        print(f"Error: Cannot read image: {input_image}")
        return
    
    # Initialize pipeline
    print("Processing image...")
    pipeline = TrainDetectionOCRPipeline()
    
    # Process
    annotated, ocr_results = pipeline.process_frame(frame)
    
    # Save result
    cv2.imwrite(output_image, annotated)
    
    # Print results
    print(f"\nDetected {len(ocr_results)} wagon(s):")
    for result in ocr_results:
        print(f"  - {result['wagon_id']} (confidence: {result['confidence']:.2f})")
    print(f"\nOutput saved to: {output_image}")


def main():
    parser = argparse.ArgumentParser(
        description="Train OCR Pipeline Demo",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process video
  python demo.py --video input.mp4 --output output.mp4
  
  # Process image
  python demo.py --image input.jpg --output output.jpg
  
  # Real-time webcam
  python demo.py --webcam
        """
    )
    
    parser.add_argument('--video', '-v', help='Input video file')
    parser.add_argument('--image', '-i', help='Input image file')
    parser.add_argument('--output', '-o', help='Output file (video or image)')
    parser.add_argument('--webcam', '-w', action='store_true', help='Use webcam')
    
    args = parser.parse_args()
    
    # Check mode
    if args.webcam:
        process_webcam_demo()
    
    elif args.video:
        if not args.output:
            args.output = 'output_annotated.mp4'
        process_video_demo(args.video, args.output)
    
    elif args.image:
        if not args.output:
            args.output = 'output_annotated.jpg'
        process_image_demo(args.image, args.output)
    
    else:
        parser.print_help()
        print("\nError: Please specify --video, --image, or --webcam")
        sys.exit(1)


if __name__ == "__main__":
    main()
