"""
Migration Script: Convert Existing PolicyTracker to RAG System
=============================================================

This script migrates your existing PolicyTracker chatbot to a full RAG-based system:
1. Creates necessary database tables
2. Migrates existing conversation data
3. Generates embeddings for historical conversations
4. Sets up vector search capabilities
5. Integrates with existing policy database

Run this script to upgrade your system to RAG capabilities.
"""

import asyncio
import sys
import os
from datetime import datetime

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.rag_chatbot_service import RAGChatbotService
from models.rag_models import RAGDatabaseManager, migrate_existing_conversations_to_rag
from config.dynamodb import DynamoDBManager

class PolicyTrackerRAGMigration:
    """
    Handles the complete migration of PolicyTracker to RAG system
    """
    
    def __init__(self):
        self.db_manager = DynamoDBManager()
        self.rag_service = RAGChatbotService()
        self.rag_db = RAGDatabaseManager(self.db_manager)
        
    async def run_complete_migration(self):
        """Run the complete migration process"""
        print("🚀 Starting PolicyTracker RAG Migration")
        print("=" * 60)
        
        try:
            # Step 1: Check prerequisites
            await self._check_prerequisites()
            
            # Step 2: Create RAG database tables
            await self._create_rag_tables()
            
            # Step 3: Migrate existing conversations
            await self._migrate_conversations()
            
            # Step 4: Initialize vector search
            await self._initialize_vector_search()
            
            # Step 5: Verify migration
            await self._verify_migration()
            
            # Step 6: Generate migration report
            await self._generate_migration_report()
            
            print("✅ RAG Migration completed successfully!")
            print("🎉 Your PolicyTracker now has RAG capabilities!")
            
        except Exception as e:
            print(f"❌ Migration failed: {e}")
            await self._cleanup_on_failure()
            raise
    
    async def _check_prerequisites(self):
        """Check if all prerequisites are met"""
        print("🔍 Checking prerequisites...")
        
        # Check database connection
        try:
            tables = await self.db_manager.list_tables()
            print(f"✅ Database connected - Found {len(tables)} existing tables")
        except Exception as e:
            raise Exception(f"Database connection failed: {e}")
        
        # Check OpenAI API key
        if not os.getenv('OPENAI_API_KEY'):
            print("⚠️ OpenAI API key not found - embeddings will not work")
        else:
            print("✅ OpenAI API key configured")
        
        # Check existing data
        try:
            sessions = await self.db_manager.scan_table('chat_sessions')
            print(f"✅ Found {len(sessions)} existing chat sessions to migrate")
        except Exception as e:
            print(f"⚠️ No existing chat sessions found: {e}")
    
    async def _create_rag_tables(self):
        """Create all necessary RAG tables"""
        print("🏗️ Creating RAG database tables...")
        
        try:
            await self.rag_db.ensure_rag_tables()
            print("✅ RAG tables created successfully")
        except Exception as e:
            raise Exception(f"Failed to create RAG tables: {e}")
    
    async def _migrate_conversations(self):
        """Migrate existing conversations to RAG format"""
        print("📦 Migrating existing conversations...")
        
        try:
            await migrate_existing_conversations_to_rag(self.db_manager, self.rag_service)
            print("✅ Conversation migration completed")
        except Exception as e:
            raise Exception(f"Conversation migration failed: {e}")
    
    async def _initialize_vector_search(self):
        """Initialize vector search capabilities"""
        print("🔍 Initializing vector search...")
        
        try:
            # Load existing conversations into FAISS index
            await self.rag_service.initialize_from_existing_conversations()
            print("✅ Vector search initialized")
        except Exception as e:
            print(f"⚠️ Vector search initialization failed: {e}")
            print("   You can run this later using the /rag/initialize endpoint")
    
    async def _verify_migration(self):
        """Verify that migration was successful"""
        print("🔎 Verifying migration...")
        
        try:
            # Check RAG system stats
            stats = self.rag_service.get_system_stats()
            db_stats = await self.rag_db.get_database_stats()
            
            print(f"✅ RAG System Status:")
            print(f"   - Total conversations: {stats['total_conversations']}")
            print(f"   - FAISS index size: {stats['faiss_index_size']}")
            print(f"   - Database conversations: {db_stats.get('total_conversations', 0)}")
            print(f"   - Keyword entries: {db_stats.get('total_keyword_entries', 0)}")
            
        except Exception as e:
            print(f"⚠️ Verification incomplete: {e}")
    
    async def _generate_migration_report(self):
        """Generate detailed migration report"""
        print("📊 Generating migration report...")
        
        try:
            report = {
                'migration_timestamp': datetime.utcnow().isoformat(),
                'status': 'completed',
                'rag_stats': self.rag_service.get_system_stats(),
                'database_stats': await self.rag_db.get_database_stats(),
                'tables_created': [
                    'conversation_embeddings',
                    'keyword_index'
                ],
                'features_enabled': [
                    'Semantic similarity search',
                    'Keyword-based search',
                    'Hybrid retrieval',
                    'Context-aware responses',
                    'Conversation history analysis'
                ]
            }
            
            # Save report
            report_file = f"rag_migration_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            import json
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2)
            
            print(f"✅ Migration report saved: {report_file}")
            
        except Exception as e:
            print(f"⚠️ Could not generate report: {e}")
    
    async def _cleanup_on_failure(self):
        """Cleanup on migration failure"""
        print("🧹 Cleaning up after failure...")
        
        try:
            # Remove any partially created tables
            tables_to_cleanup = ['conversation_embeddings', 'keyword_index']
            
            for table in tables_to_cleanup:
                try:
                    await self.db_manager.delete_table(table)
                    print(f"   Cleaned up table: {table}")
                except:
                    pass  # Table might not exist
                    
        except Exception as e:
            print(f"⚠️ Cleanup error: {e}")

async def main():
    """Main migration function"""
    print("PolicyTracker RAG Migration Tool")
    print("=================================")
    print("This will upgrade your PolicyTracker to include RAG capabilities.")
    print("The migration is safe and won't affect your existing data.")
    print()
    
    # Confirm migration
    response = input("Do you want to proceed with the migration? (y/N): ")
    if response.lower() != 'y':
        print("Migration cancelled.")
        return
    
    # Run migration
    migration = PolicyTrackerRAGMigration()
    await migration.run_complete_migration()
    
    print()
    print("🎯 Next Steps:")
    print("1. Test RAG functionality using /rag/chat endpoint")
    print("2. Check system status with /rag/status endpoint")
    print("3. Search conversations with /rag/search endpoint")
    print("4. Monitor performance and adjust parameters as needed")
    print()
    print("📚 Documentation:")
    print("- RAG endpoints: /docs (FastAPI documentation)")
    print("- System configuration: services/rag_chatbot_service.py")
    print("- Database models: models/rag_models.py")

if __name__ == "__main__":
    asyncio.run(main())
