#!/usr/bin/env python3
"""
Test script to verify Qdrant connection and search capabilities
"""

import os
import sys
from pathlib import Path

# Add current directory to path
sys.path.append(str(Path(__file__).parent))

def test_qdrant_connection():
    """Test connection to Qdrant and search capabilities"""
    print("🔍 Testing Qdrant Connection...")
    
    try:
        from rag_ingestion_service.vector_store import VectorStore
        from rag_ingestion_service.embedding_generator import EmbeddingGenerator
        
        # Get Qdrant credentials
        qdrant_api_key = os.getenv('QDRANT_API_KEY')
        qdrant_url = os.getenv('QDRANT_URL', 'https://9becb4cf-82b6-456f-ae0c-d797c6c946cc.us-east4-0.gcp.cloud.qdrant.io')
        
        if not qdrant_api_key:
            print("❌ QDRANT_API_KEY not set")
            return False
        
        print(f"   Qdrant URL: {qdrant_url}")
        
        # Initialize vector store
        vector_store = VectorStore(qdrant_api_key, qdrant_url)
        
        # List collections
        collections = vector_store.list_collections()
        print(f"✅ Connected to Qdrant")
        print(f"   Collections found: {len(collections)}")
        
        for collection in collections:
            info = vector_store.get_collection_info(collection)
            print(f"   - {collection}: {info.get('points_count', 'Unknown')} points")
        
        # Test search in the existing collection
        existing_collection = "book_computer_application_ncert_class_xii"
        if existing_collection in collections:
            print(f"\n🔍 Testing search in {existing_collection}...")
            
            # Generate embedding for a test query
            embedding_gen = EmbeddingGenerator()
            test_query = "computer applications questions"
            query_embedding = embedding_gen.generate_embedding(test_query)
            
            # Search
            results = vector_store.search_similar(
                collection_name=existing_collection,
                query_embedding=query_embedding,
                limit=3,
                score_threshold=0.7
            )
            
            print(f"   Search query: '{test_query}'")
            print(f"   Results found: {len(results)}")
            
            for i, result in enumerate(results, 1):
                print(f"   {i}. Score: {result['score']:.3f}")
                print(f"      Content: {result['content'][:100]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Error connecting to Qdrant: {str(e)}")
        return False

def test_question_analysis_service():
    """Test the question analysis service components"""
    print("\n🧪 Testing Question Analysis Service...")
    
    try:
        from question_analysis_service.batch_processor import BatchQuestionProcessor
        
        # Get API keys
        gemini_api_key = os.getenv('GEMINI_API_KEY')
        qdrant_api_key = os.getenv('QDRANT_API_KEY')
        
        if not gemini_api_key:
            print("❌ GEMINI_API_KEY not set, skipping analysis test")
            return False
        
        if not qdrant_api_key:
            print("❌ QDRANT_API_KEY not set, skipping analysis test")
            return False
        
        # Initialize processor
        processor = BatchQuestionProcessor(
            gemini_api_key=gemini_api_key,
            qdrant_api_key=qdrant_api_key,
            qdrant_url=os.getenv('QDRANT_URL'),
            gcp_project_id=os.getenv('GCP_PROJECT_ID', 'book-qc-cf'),
            bucket_name=os.getenv('BUCKET_NAME', 'book-qc-cf-pdf-storage')
        )
        
        print("✅ Question Analysis Service initialized successfully")
        
        # Test collection creation
        collection_name = "question_analysis_results"
        success = processor.create_analysis_collection()
        if success:
            print(f"✅ Analysis collection '{collection_name}' ready")
        else:
            print(f"⚠️  Analysis collection '{collection_name}' may already exist")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing question analysis service: {str(e)}")
        return False

def main():
    """Main test function"""
    print("🚀 Qdrant Connection and Service Test")
    print("=" * 50)
    
    # Check environment
    print("🔍 Environment Check:")
    print(f"   GEMINI_API_KEY: {'✅ Set' if os.getenv('GEMINI_API_KEY') else '❌ Not set'}")
    print(f"   QDRANT_API_KEY: {'✅ Set' if os.getenv('QDRANT_API_KEY') else '❌ Not set'}")
    print(f"   GCP_PROJECT_ID: {os.getenv('GCP_PROJECT_ID', 'Not set')}")
    print(f"   BUCKET_NAME: {os.getenv('BUCKET_NAME', 'Not set')}")
    print()
    
    # Test Qdrant connection
    qdrant_ok = test_qdrant_connection()
    
    # Test question analysis service
    service_ok = test_question_analysis_service()
    
    print("\n📊 Test Results:")
    print(f"   Qdrant Connection: {'✅ Pass' if qdrant_ok else '❌ Fail'}")
    print(f"   Analysis Service: {'✅ Pass' if service_ok else '❌ Fail'}")
    
    if qdrant_ok and service_ok:
        print("\n🎉 All tests passed! The service is ready to use.")
        print("\n💡 Next steps:")
        print("   1. Run: python analyze_questions_demo.py")
        print("   2. Or use CLI: python question_analysis_service/cli_main.py --help")
    else:
        print("\n❌ Some tests failed. Please check the errors above.")

if __name__ == '__main__':
    main()
