#!/usr/bin/env python3
"""
Integration Test Suite for NotebookLlama RAGFlow Integration

This script validates that the RAGFlow integration works correctly
and doesn't break existing NotebookLlama functionality.
"""

import os
import sys
import asyncio
import pytest
import logging
from typing import Dict, Any, List
import tempfile
from pathlib import Path
import json

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class IntegrationTest:
    """Test suite for RAGFlow integration"""
    
    def __init__(self):
        self.test_results = []
        
    def add_result(self, test_name: str, success: bool, message: str, error: str = None):
        """Record test result"""
        self.test_results.append({
            "test": test_name,
            "success": success,
            "message": message,
            "error": error
        })
        
        icon = "✅" if success else "❌"
        logger.info(f"{icon} {test_name}: {message}")
        
        if error:
            logger.error(f"   Error: {error}")
    
    async def test_existing_functionality(self) -> bool:
        """Test that existing NotebookLlama functionality still works"""
        try:
            # Test basic imports
            from src.notebookllama import utils, models, documents
            self.add_result("Import Core Modules", True, "All core modules imported successfully")
            
            # Test document management
            from src.notebookllama.documents import DocumentManager
            doc_manager = DocumentManager()
            self.add_result("Document Manager Init", True, "DocumentManager created successfully")
            
            # Test models
            from src.notebookllama.models import get_model_provider
            model_provider = get_model_provider()
            if model_provider:
                self.add_result("Model Provider", True, "Model provider initialized")
            else:
                self.add_result("Model Provider", False, "No model provider available")
            
            # Test MCP server
            from src.notebookllama.server import create_mcp_server
            server = create_mcp_server()
            self.add_result("MCP Server", True, "MCP server created successfully")
            
            return True
            
        except Exception as e:
            self.add_result("Existing Functionality", False, "Failed to load existing functionality", str(e))
            return False
    
    async def test_ragflow_integration(self) -> bool:
        """Test RAGFlow integration components"""
        try:
            # Test main integration module
            from src.notebookllama.ragflow_integration import RAGFlowIntegration
            
            integration = RAGFlowIntegration()
            features = integration.get_available_features()
            
            self.add_result("RAGFlow Integration", True, f"Integration loaded - {len(features)} features available")
            
            # Test enhanced document manager
            if integration.is_supabase_available():
                from src.notebookllama.documents import EnhancedDocumentManager
                enhanced_manager = EnhancedDocumentManager()
                self.add_result("Enhanced Document Manager", True, "Enhanced document manager created")
            else:
                self.add_result("Enhanced Document Manager", False, "Supabase not configured - enhanced features unavailable")
            
            return True
            
        except ImportError as e:
            self.add_result("RAGFlow Integration", False, "RAGFlow integration not available", str(e))
            return False
        except Exception as e:
            self.add_result("RAGFlow Integration", False, "RAGFlow integration error", str(e))
            return False
    
    async def test_client_modules(self) -> Dict[str, bool]:
        """Test individual RAG client modules"""
        clients = {}
        
        # Test Supabase client
        try:
            from src.notebookllama.rag_clients.supabase_client import create_supabase_client
            if os.getenv("SUPABASE_URL") and os.getenv("SUPABASE_KEY"):
                client = create_supabase_client()
                if client:
                    clients["supabase"] = True
                    self.add_result("Supabase Client", True, "Client created and connected")
                else:
                    clients["supabase"] = False
                    self.add_result("Supabase Client", False, "Could not create client")
            else:
                clients["supabase"] = False
                self.add_result("Supabase Client", False, "No credentials configured")
        except ImportError:
            clients["supabase"] = False
            self.add_result("Supabase Client", False, "Module not available")
        except Exception as e:
            clients["supabase"] = False
            self.add_result("Supabase Client", False, "Client error", str(e))
        
        # Test Graphiti client
        try:
            from src.notebookllama.rag_clients.graphiti_client import create_graphiti_client
            if os.getenv("NEO4J_PASSWORD"):
                client = create_graphiti_client()
                if client:
                    clients["graphiti"] = True
                    self.add_result("Graphiti Client", True, "Client created")
                else:
                    clients["graphiti"] = False
                    self.add_result("Graphiti Client", False, "Could not create client")
            else:
                clients["graphiti"] = False
                self.add_result("Graphiti Client", False, "No Neo4j password configured")
        except ImportError:
            clients["graphiti"] = False
            self.add_result("Graphiti Client", False, "Module not available")
        except Exception as e:
            clients["graphiti"] = False
            self.add_result("Graphiti Client", False, "Client error", str(e))
        
        # Test Crawl4AI
        try:
            from src.notebookllama.rag_clients.crawl_manager import CrawlManager
            crawl_manager = CrawlManager()
            clients["crawl4ai"] = True
            self.add_result("Crawl4AI", True, "Crawl manager created")
        except ImportError:
            clients["crawl4ai"] = False
            self.add_result("Crawl4AI", False, "Module not available")
        except Exception as e:
            clients["crawl4ai"] = False
            self.add_result("Crawl4AI", False, "Crawl manager error", str(e))
        
        # Test LLM provider
        try:
            from src.notebookllama.rag_clients.llm_provider import get_llm_provider
            llm = get_llm_provider()
            providers = llm.get_available_providers()
            if providers:
                clients["llm"] = True
                self.add_result("LLM Provider", True, f"{len(providers)} providers available")
            else:
                clients["llm"] = False
                self.add_result("LLM Provider", False, "No providers configured")
        except ImportError:
            clients["llm"] = False
            self.add_result("LLM Provider", False, "Module not available")
        except Exception as e:
            clients["llm"] = False
            self.add_result("LLM Provider", False, "Provider error", str(e))
        
        return clients
    
    async def test_enhanced_features(self) -> bool:
        """Test enhanced document processing features"""
        if not (os.getenv("SUPABASE_URL") and os.getenv("SUPABASE_KEY")):
            self.add_result("Enhanced Features", False, "Supabase not configured - skipping enhanced tests")
            return False
        
        try:
            from src.notebookllama.documents import EnhancedDocumentManager
            
            # Create test document
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                f.write("This is a test document for RAGFlow integration testing. It contains sample content for vector search.")
                test_file = f.name
            
            try:
                enhanced_manager = EnhancedDocumentManager()
                
                # Test document processing
                doc = await enhanced_manager.add_document(test_file, enable_rag=True)
                if doc:
                    self.add_result("Enhanced Document Processing", True, "Document processed with RAG features")
                    
                    # Test search
                    results = await enhanced_manager.search_documents("test document", method="hybrid")
                    if results:
                        self.add_result("Enhanced Search", True, f"Found {len(results)} results")
                    else:
                        self.add_result("Enhanced Search", False, "No search results")
                    
                    return True
                else:
                    self.add_result("Enhanced Document Processing", False, "Failed to process document")
                    return False
                    
            finally:
                # Cleanup
                os.unlink(test_file)
                
        except Exception as e:
            self.add_result("Enhanced Features", False, "Enhanced features test failed", str(e))
            return False
    
    async def test_mcp_server_tools(self) -> bool:
        """Test that MCP server tools work with RAG integration"""
        try:
            from src.notebookllama.server import create_mcp_server
            
            server = create_mcp_server()
            
            # Get available tools
            tools = server.list_tools()
            tool_names = [tool.name for tool in tools]
            
            # Check for base tools
            base_tools = ["search_documents", "add_document", "list_documents"]
            has_base_tools = all(tool in tool_names for tool in base_tools)
            
            if has_base_tools:
                self.add_result("MCP Base Tools", True, "All base tools available")
            else:
                missing = [tool for tool in base_tools if tool not in tool_names]
                self.add_result("MCP Base Tools", False, f"Missing tools: {missing}")
            
            # Check for enhanced tools
            if os.getenv("SUPABASE_URL") or os.getenv("NEO4J_PASSWORD"):
                enhanced_tools = ["enhanced_search", "crawl_and_process"]
                has_enhanced_tools = any(tool in tool_names for tool in enhanced_tools)
                
                if has_enhanced_tools:
                    self.add_result("MCP Enhanced Tools", True, "Enhanced tools available")
                else:
                    self.add_result("MCP Enhanced Tools", False, "No enhanced tools found")
            else:
                self.add_result("MCP Enhanced Tools", False, "No RAG services configured")
            
            return has_base_tools
            
        except Exception as e:
            self.add_result("MCP Server Tools", False, "MCP server test failed", str(e))
            return False
    
    async def test_streamlit_pages(self) -> bool:
        """Test that Streamlit pages load correctly"""
        try:
            # Test existing pages
            existing_pages = [
                "src.notebookllama.pages.1_Document_Management_UI",
                "src.notebookllama.pages.2_Document_Chat",
                "src.notebookllama.pages.3_Interactive_Table_and_Plot_Visualization",
                "src.notebookllama.pages.4_Observability_Dashboard"
            ]
            
            for page in existing_pages:
                try:
                    __import__(page)
                    self.add_result(f"Streamlit Page: {page.split('.')[-1]}", True, "Page loads successfully")
                except Exception as e:
                    self.add_result(f"Streamlit Page: {page.split('.')[-1]}", False, "Page failed to load", str(e))
            
            # Test new RAG page
            try:
                from src.notebookllama.pages import Enhanced_RAG_Chat
                self.add_result("Streamlit Page: Enhanced_RAG_Chat", True, "RAG page loads successfully")
            except Exception as e:
                self.add_result("Streamlit Page: Enhanced_RAG_Chat", False, "RAG page failed to load", str(e))
            
            return True
            
        except Exception as e:
            self.add_result("Streamlit Pages", False, "Streamlit page test failed", str(e))
            return False
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run complete integration test suite"""
        print("🧪 Running NotebookLlama RAGFlow Integration Tests")
        print("=" * 60)
        
        # Run test categories
        tests = [
            ("Existing Functionality", self.test_existing_functionality()),
            ("RAGFlow Integration", self.test_ragflow_integration()),
            ("Client Modules", self.test_client_modules()),
            ("Enhanced Features", self.test_enhanced_features()),
            ("MCP Server Tools", self.test_mcp_server_tools()),
            ("Streamlit Pages", self.test_streamlit_pages())
        ]
        
        results = {}
        for name, test_coro in tests:
            print(f"\n🔍 Testing {name}...")
            try:
                results[name] = await test_coro
            except Exception as e:
                logger.error(f"Test category {name} failed: {e}")
                results[name] = False
        
        # Calculate summary
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        
        print("\n" + "=" * 60)
        print("📊 Integration Test Summary")
        print("=" * 60)
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {total_tests - passed_tests}")
        print(f"📈 Success Rate: {passed_tests/total_tests*100:.1f}%")
        
        # Failed tests
        failed_tests = [r for r in self.test_results if not r["success"]]
        if failed_tests:
            print(f"\n❌ Failed Tests ({len(failed_tests)}):")
            for test in failed_tests:
                print(f"  • {test['test']}: {test['message']}")
                if test['error']:
                    print(f"    Error: {test['error']}")
        
        print("\n🎯 Integration Status:")
        if passed_tests == total_tests:
            print("  ✅ Perfect integration - all tests passed")
        elif passed_tests / total_tests >= 0.8:
            print("  ✅ Good integration - most features working")
        elif passed_tests / total_tests >= 0.6:
            print("  ⚠️  Partial integration - some issues need attention")
        else:
            print("  ❌ Poor integration - significant issues detected")
        
        return {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "success_rate": passed_tests / total_tests,
            "test_results": self.test_results,
            "category_results": results
        }


async def main():
    """Main test function"""
    test_suite = IntegrationTest()
    
    try:
        # Load environment variables
        from dotenv import load_dotenv
        load_dotenv()
        
        # Run tests
        results = await test_suite.run_all_tests()
        
        # Save results
        results_file = "integration_test_results.json"
        with open(results_file, "w") as f:
            json.dump(results, f, indent=2)
        
        print(f"\n💾 Test results saved to: {results_file}")
        
        if results["success_rate"] < 0.8:
            print("\n⚠️  Integration tests reveal issues. Please review failed tests.")
            sys.exit(1)
        else:
            print("\n✅ Integration tests passed successfully!")
            
    except KeyboardInterrupt:
        print("\n⛔ Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Test suite failed with error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())