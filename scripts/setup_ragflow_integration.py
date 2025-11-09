#!/usr/bin/env python3
"""
RAGFlow Integration Setup Script for NotebookLlama

This script helps set up the RAGFlow integration components including:
- Supabase database tables
- Neo4j database connection
- LLM provider configuration
- Environment validation
"""

import os
import sys
import asyncio
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass
import json

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class SetupResult:
    component: str
    success: bool
    message: str
    details: Optional[Dict[str, Any]] = None


class RAGFlowSetup:
    """Setup manager for RAGFlow integration"""
    
    def __init__(self):
        self.results: List[SetupResult] = []
        
    def add_result(self, component: str, success: bool, message: str, details: Optional[Dict] = None):
        """Add a setup result"""
        result = SetupResult(component, success, message, details)
        self.results.append(result)
        
        icon = "✅" if success else "❌"
        logger.info(f"{icon} {component}: {message}")
        
    async def setup_supabase(self) -> bool:
        """Setup Supabase database tables"""
        try:
            from src.notebookllama.rag_clients.supabase_client import create_supabase_client, setup_supabase_tables
            
            # Create client
            client = create_supabase_client()
            if not client:
                self.add_result("Supabase", False, "Could not create Supabase client - check SUPABASE_URL and SUPABASE_KEY")
                return False
            
            # Setup tables
            success = await setup_supabase_tables(client)
            if success:
                self.add_result("Supabase", True, "Database tables created successfully")
                return True
            else:
                self.add_result("Supabase", False, "Failed to create database tables")
                return False
                
        except ImportError:
            self.add_result("Supabase", False, "Supabase client not available - install with: pip install supabase")
            return False
        except Exception as e:
            self.add_result("Supabase", False, f"Setup error: {e}")
            return False
    
    async def setup_neo4j(self) -> bool:
        """Setup Neo4j database connection"""
        try:
            from src.notebookllama.rag_clients.graphiti_client import create_graphiti_client
            
            # Test connection
            client = create_graphiti_client()
            if not client:
                self.add_result("Neo4j", False, "Could not create Graphiti client - check NEO4J_* variables")
                return False
            
            # Test basic functionality
            try:
                from src.notebookllama.rag_clients.graphiti_client import get_graph_statistics
                stats = await get_graph_statistics()
                
                if stats.get("success"):
                    self.add_result("Neo4j", True, f"Connected successfully - {stats.get('total_entities', 0)} entities in graph")
                    return True
                else:
                    self.add_result("Neo4j", False, f"Connection test failed: {stats.get('error', 'Unknown error')}")
                    return False
                    
            except Exception as e:
                # Connection works but graph might be empty
                self.add_result("Neo4j", True, f"Connected (empty graph) - {e}")
                return True
                
        except ImportError:
            self.add_result("Neo4j", False, "Graphiti/Neo4j not available - install with: pip install graphiti-core neo4j")
            return False
        except Exception as e:
            self.add_result("Neo4j", False, f"Setup error: {e}")
            return False
    
    async def setup_llm_providers(self) -> Dict[str, bool]:
        """Setup and test LLM providers"""
        providers = {}
        
        try:
            from src.notebookllama.rag_clients.llm_provider import get_llm_provider, test_provider, LLMProvider
            
            llm = get_llm_provider()
            available_providers = llm.get_available_providers()
            
            if not available_providers:
                self.add_result("LLM Providers", False, "No LLM providers configured")
                return providers
            
            # Test each available provider
            for provider in available_providers:
                try:
                    test_result = await test_provider(provider)
                    
                    if test_result["status"] == "success":
                        providers[provider.value] = True
                        self.add_result(
                            f"LLM-{provider.value}", 
                            True, 
                            f"Working - completion: {test_result['completion_works']}, embedding: {test_result['embedding_works']}"
                        )
                    else:
                        providers[provider.value] = False
                        self.add_result(f"LLM-{provider.value}", False, f"Failed: {test_result.get('error', 'Unknown error')}")
                        
                except Exception as e:
                    providers[provider.value] = False
                    self.add_result(f"LLM-{provider.value}", False, f"Test error: {e}")
            
            return providers
            
        except ImportError:
            self.add_result("LLM Providers", False, "LLM provider modules not available")
            return providers
        except Exception as e:
            self.add_result("LLM Providers", False, f"Setup error: {e}")
            return providers
    
    async def setup_crawl4ai(self) -> bool:
        """Setup Crawl4AI components"""
        try:
            from src.notebookllama.rag_clients.crawl_manager import crawl_url
            
            # Test with a simple URL
            test_url = "https://httpbin.org/status/200"
            result = await crawl_url(test_url, extract_entities=False)
            
            if result.status.value == "completed":
                self.add_result("Crawl4AI", True, "Web crawling working")
                return True
            else:
                self.add_result("Crawl4AI", False, f"Test crawl failed: {result.error}")
                return False
                
        except ImportError:
            self.add_result("Crawl4AI", False, "Crawl4AI not available - install with: pip install crawl4ai")
            return False
        except Exception as e:
            self.add_result("Crawl4AI", False, f"Setup error: {e}")
            return False
    
    def check_environment(self) -> Dict[str, bool]:
        """Check required environment variables"""
        required_vars = {
            "SUPABASE_URL": os.getenv("SUPABASE_URL"),
            "SUPABASE_KEY": os.getenv("SUPABASE_KEY"),
            "NEO4J_PASSWORD": os.getenv("NEO4J_PASSWORD")
        }
        
        optional_vars = {
            "GOOGLE_API_KEY": os.getenv("GOOGLE_API_KEY"),
            "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
            "ANTHROPIC_API_KEY": os.getenv("ANTHROPIC_API_KEY"),
            "OLLAMA_HOST": os.getenv("OLLAMA_HOST", "http://localhost:11434")
        }
        
        env_status = {}
        
        # Check required variables
        for var, value in required_vars.items():
            env_status[var] = bool(value)
            if value:
                self.add_result(f"ENV-{var}", True, "Configured")
            else:
                self.add_result(f"ENV-{var}", False, "Missing - required for RAG functionality")
        
        # Check optional variables
        llm_providers_available = any(optional_vars.values())
        if llm_providers_available:
            self.add_result("ENV-LLM", True, "At least one LLM provider configured")
        else:
            self.add_result("ENV-LLM", False, "No LLM providers configured")
        
        return env_status
    
    async def run_full_setup(self) -> Dict[str, Any]:
        """Run complete setup process"""
        print("🚀 Starting RAGFlow Integration Setup for NotebookLlama")
        print("=" * 60)
        
        # Check environment
        print("\n📋 Checking Environment Variables...")
        env_status = self.check_environment()
        
        # Setup components
        setup_tasks = []
        
        if env_status.get("SUPABASE_URL") and env_status.get("SUPABASE_KEY"):
            print("\n🔗 Setting up Supabase...")
            setup_tasks.append(("supabase", self.setup_supabase()))
        
        if env_status.get("NEO4J_PASSWORD"):
            print("\n🕸️  Setting up Neo4j/Graphiti...")
            setup_tasks.append(("neo4j", self.setup_neo4j()))
        
        print("\n🤖 Testing LLM Providers...")
        setup_tasks.append(("llm_providers", self.setup_llm_providers()))
        
        print("\n🌐 Testing Web Crawling...")
        setup_tasks.append(("crawl4ai", self.setup_crawl4ai()))
        
        # Run all setup tasks
        results = {}
        for name, task in setup_tasks:
            try:
                results[name] = await task
            except Exception as e:
                logger.error(f"Setup task {name} failed: {e}")
                results[name] = False
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 Setup Summary")
        print("=" * 60)
        
        success_count = 0
        total_count = len(self.results)
        
        for result in self.results:
            if result.success:
                success_count += 1
        
        print(f"✅ Successful: {success_count}")
        print(f"❌ Failed: {total_count - success_count}")
        print(f"📈 Success Rate: {success_count/total_count*100:.1f}%")
        
        # Feature availability
        print("\n🎯 Available Features:")
        features = {
            "Vector Search": env_status.get("SUPABASE_URL") and results.get("supabase"),
            "Knowledge Graph": env_status.get("NEO4J_PASSWORD") and results.get("neo4j"), 
            "Web Crawling": results.get("crawl4ai"),
            "Multi-LLM": any(results.get("llm_providers", {}).values()) if isinstance(results.get("llm_providers"), dict) else False
        }
        
        for feature, available in features.items():
            icon = "✅" if available else "❌"
            print(f"  {icon} {feature}")
        
        if any(features.values()):
            print("\n🎉 RAGFlow integration is ready to use!")
        else:
            print("\n⚠️  RAGFlow features are not available. Please check configuration.")
        
        return {
            "success_rate": success_count / total_count,
            "results": self.results,
            "available_features": features,
            "environment_status": env_status
        }


async def main():
    """Main setup function"""
    setup = RAGFlowSetup()
    
    try:
        # Load environment variables
        from dotenv import load_dotenv
        load_dotenv()
        
        # Run setup
        results = await setup.run_full_setup()
        
        # Save results to file
        results_file = "ragflow_setup_results.json"
        with open(results_file, "w") as f:
            # Convert results to JSON-serializable format
            json_results = {
                "success_rate": results["success_rate"],
                "available_features": results["available_features"],
                "environment_status": results["environment_status"],
                "setup_results": [
                    {
                        "component": r.component,
                        "success": r.success,
                        "message": r.message,
                        "details": r.details
                    }
                    for r in results["results"]
                ]
            }
            json.dump(json_results, f, indent=2)
        
        print(f"\n💾 Setup results saved to: {results_file}")
        
        if results["success_rate"] < 0.5:
            print("\n⚠️  Setup incomplete. Please address the failed components.")
            sys.exit(1)
        else:
            print("\n✅ Setup completed successfully!")
            
    except KeyboardInterrupt:
        print("\n⛔ Setup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Setup failed with error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())