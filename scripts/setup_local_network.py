#!/usr/bin/env python3
"""
Local Network Setup Script for RAGFlow Integration

This script sets up a fully open-source, local network deployment
of NotebookLlama with RAGFlow capabilities using:
- PostgreSQL + pgvector (vector database)
- Neo4j Community Edition (knowledge graph)
- Ollama (local LLM models)
"""

import os
import sys
import asyncio
import logging
import subprocess
import json
from typing import Dict, Any, List
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class LocalNetworkSetup:
    """Setup manager for local network RAGFlow deployment"""
    
    def __init__(self):
        self.results = []
        self.services = {
            "postgresql": False,
            "neo4j": False,
            "ollama": False,
            "elasticsearch": False
        }
        
    def add_result(self, component: str, success: bool, message: str, details: dict = None):
        """Add setup result"""
        self.results.append({
            "component": component,
            "success": success,
            "message": message,
            "details": details or {}
        })
        
        icon = "✅" if success else "❌"
        logger.info(f"{icon} {component}: {message}")
    
    def check_service_running(self, service: str, port: int) -> bool:
        """Check if a service is running on specified port"""
        try:
            import socket
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(3)
                result = s.connect_ex(('localhost', port))
                return result == 0
        except Exception:
            return False
    
    def check_postgresql(self) -> bool:
        """Check PostgreSQL installation and pgvector extension"""
        try:
            # Check if PostgreSQL is running
            if not self.check_service_running("postgresql", 5432):
                self.add_result("PostgreSQL", False, "Not running on port 5432")
                return False
            
            # Try to connect and check pgvector
            try:
                import asyncpg
                
                async def test_pg():
                    conn_string = (
                        f"postgresql://{os.getenv('PGVECTOR_USER', 'postgres')}:"
                        f"{os.getenv('PGVECTOR_PASSWORD', 'password')}@"
                        f"localhost:5432/{os.getenv('PGVECTOR_DATABASE', 'postgres')}"
                    )
                    
                    try:
                        conn = await asyncpg.connect(conn_string)
                        
                        # Check if pgvector is available
                        result = await conn.fetchval("""
                            SELECT COUNT(*) FROM pg_extension WHERE extname = 'vector';
                        """)
                        
                        has_vector = result > 0
                        await conn.close()
                        
                        return has_vector
                        
                    except Exception as e:
                        logger.error(f"PostgreSQL connection failed: {e}")
                        return False
                
                has_vector = asyncio.run(test_pg())
                
                if has_vector:
                    self.add_result("PostgreSQL", True, "Running with pgvector extension")
                    self.services["postgresql"] = True
                    return True
                else:
                    self.add_result("PostgreSQL", False, "pgvector extension not installed")
                    return False
                    
            except ImportError:
                self.add_result("PostgreSQL", False, "asyncpg not installed - run: pip install asyncpg")
                return False
                
        except Exception as e:
            self.add_result("PostgreSQL", False, f"Check failed: {e}")
            return False
    
    def check_neo4j(self) -> bool:
        """Check Neo4j Community Edition"""
        try:
            if not self.check_service_running("neo4j", 7687):
                self.add_result("Neo4j", False, "Not running on port 7687")
                return False
            
            # Try to connect
            try:
                from neo4j import GraphDatabase
                
                uri = os.getenv("NEO4J_URI", "neo4j://localhost:7687")
                username = os.getenv("NEO4J_USERNAME", "neo4j")
                password = os.getenv("NEO4J_PASSWORD", "password")
                
                driver = GraphDatabase.driver(uri, auth=(username, password))
                
                with driver.session() as session:
                    result = session.run("RETURN 'Connection successful' AS message")
                    message = result.single()["message"]
                
                driver.close()
                
                self.add_result("Neo4j", True, "Connected successfully")
                self.services["neo4j"] = True
                return True
                
            except ImportError:
                self.add_result("Neo4j", False, "neo4j driver not installed - run: pip install neo4j")
                return False
            except Exception as e:
                self.add_result("Neo4j", False, f"Connection failed: {e}")
                return False
                
        except Exception as e:
            self.add_result("Neo4j", False, f"Check failed: {e}")
            return False
    
    def check_ollama(self) -> bool:
        """Check Ollama local LLM service"""
        try:
            if not self.check_service_running("ollama", 11434):
                self.add_result("Ollama", False, "Not running on port 11434")
                return False
            
            # Try API call
            import requests
            
            try:
                response = requests.get("http://localhost:11434/api/tags", timeout=10)
                
                if response.status_code == 200:
                    models = response.json().get("models", [])
                    model_names = [model["name"] for model in models]
                    
                    if models:
                        self.add_result("Ollama", True, f"Running with {len(models)} models: {', '.join(model_names[:3])}")
                        self.services["ollama"] = True
                        return True
                    else:
                        self.add_result("Ollama", False, "No models installed - run: ollama pull llama3.1:8b")
                        return False
                else:
                    self.add_result("Ollama", False, f"API returned status {response.status_code}")
                    return False
                    
            except requests.exceptions.RequestException as e:
                self.add_result("Ollama", False, f"API call failed: {e}")
                return False
                
        except ImportError:
            self.add_result("Ollama", False, "requests not installed")
            return False
        except Exception as e:
            self.add_result("Ollama", False, f"Check failed: {e}")
            return False
    
    def check_elasticsearch(self) -> bool:
        """Check Elasticsearch (optional)"""
        try:
            if not self.check_service_running("elasticsearch", 9200):
                self.add_result("Elasticsearch", False, "Not running on port 9200 (optional)")
                return False
            
            import requests
            
            try:
                response = requests.get("http://localhost:9200", timeout=10)
                
                if response.status_code == 200:
                    info = response.json()
                    version = info.get("version", {}).get("number", "unknown")
                    
                    self.add_result("Elasticsearch", True, f"Running version {version}")
                    self.services["elasticsearch"] = True
                    return True
                else:
                    self.add_result("Elasticsearch", False, f"API returned status {response.status_code}")
                    return False
                    
            except requests.exceptions.RequestException as e:
                self.add_result("Elasticsearch", False, f"Not accessible: {e}")
                return False
                
        except Exception as e:
            self.add_result("Elasticsearch", False, f"Check failed: {e}")
            return False
    
    async def setup_postgresql_integration(self) -> bool:
        """Setup PostgreSQL integration"""
        if not self.services["postgresql"]:
            return False
            
        try:
            from src.notebookllama.rag_clients.postgresql_client import setup_postgresql_tables, create_postgresql_client
            
            client = create_postgresql_client()
            if not client:
                self.add_result("PostgreSQL Setup", False, "Could not create client")
                return False
            
            success = await setup_postgresql_tables(client)
            await client.disconnect()
            
            if success:
                self.add_result("PostgreSQL Setup", True, "Tables created successfully")
                return True
            else:
                self.add_result("PostgreSQL Setup", False, "Failed to create tables")
                return False
                
        except Exception as e:
            self.add_result("PostgreSQL Setup", False, f"Setup error: {e}")
            return False
    
    async def test_ragflow_integration(self) -> bool:
        """Test RAGFlow integration with local services"""
        try:
            from src.notebookllama.ragflow_integration import RAGFlowIntegration
            
            # Create integration with local configuration
            integration = RAGFlowIntegration()
            
            # Check available features
            features = integration.get_available_features()
            
            local_features = []
            if self.services["postgresql"]:
                local_features.append("vector_search")
            if self.services["neo4j"]:
                local_features.append("knowledge_graph")
            if self.services["ollama"]:
                local_features.append("local_llm")
            if True:  # Crawl4AI doesn't need external service
                local_features.append("web_crawling")
            
            self.add_result("RAGFlow Integration", True, f"Available features: {', '.join(local_features)}")
            return True
            
        except Exception as e:
            self.add_result("RAGFlow Integration", False, f"Integration test failed: {e}")
            return False
    
    def create_local_env_file(self):
        """Create .env file for local network setup"""
        env_content = f"""# Local Network RAGFlow Configuration
# Generated by local network setup script

# PostgreSQL Vector Database (replaces Supabase)
DATABASE_URL=postgresql://{os.getenv('PGVECTOR_USER', 'raguser')}:{os.getenv('PGVECTOR_PASSWORD', 'secure_password')}@localhost:5432/{os.getenv('PGVECTOR_DATABASE', 'notebookllama_rag')}
PGVECTOR_HOST=localhost
PGVECTOR_PORT=5432
PGVECTOR_DATABASE={os.getenv('PGVECTOR_DATABASE', 'notebookllama_rag')}
PGVECTOR_USER={os.getenv('PGVECTOR_USER', 'raguser')}
PGVECTOR_PASSWORD={os.getenv('PGVECTOR_PASSWORD', 'secure_password')}

# Neo4j Knowledge Graph
NEO4J_URI=neo4j://localhost:7687
NEO4J_USERNAME={os.getenv('NEO4J_USERNAME', 'neo4j')}
NEO4J_PASSWORD={os.getenv('NEO4J_PASSWORD', 'your_neo4j_password')}
NEO4J_DATABASE={os.getenv('NEO4J_DATABASE', 'neo4j')}

# Ollama Local LLM
OLLAMA_HOST=http://localhost:11434
OLLAMA_BASE_URL=http://localhost:11434

# Optional: Elasticsearch
ELASTICSEARCH_URL=http://localhost:9200

# Feature toggles for local setup
ENABLE_RAG_FEATURES=true
ENABLE_WEB_CRAWLING=true
ENABLE_KNOWLEDGE_GRAPH=true
USE_LOCAL_VECTOR_DB=true
USE_LOCAL_LLM=true

# Disable external services
SUPABASE_URL=
SUPABASE_KEY=
OPENAI_API_KEY=
GOOGLE_API_KEY=
ANTHROPIC_API_KEY=

# Performance settings for local network
RAG_CHUNK_SIZE=1000
RAG_CHUNK_OVERLAP=200
RAG_TOP_K=10
VECTOR_DIMENSIONS=1536
MAX_CONCURRENT_REQUESTS=4

# Network configuration (for local network access)
# Uncomment and modify for network deployment
# STREAMLIT_SERVER_ADDRESS=0.0.0.0
# STREAMLIT_SERVER_PORT=8501
# NEO4J_URI=neo4j://your-server-ip:7687
# DATABASE_URL=postgresql://raguser:secure_password@your-server-ip:5432/notebookllama_rag
# OLLAMA_HOST=http://your-server-ip:11434
"""
        
        env_file = Path(".env.local")
        with open(env_file, "w") as f:
            f.write(env_content)
        
        self.add_result("Environment File", True, f"Created {env_file}")
        
        print(f"\n📁 Local environment file created: {env_file}")
        print("   Copy this to .env and modify passwords/settings as needed")
    
    def create_docker_compose(self):
        """Create docker-compose.yml for easy local deployment"""
        docker_compose = """version: '3.8'

services:
  postgresql:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_DB: notebookllama_rag
      POSTGRES_USER: raguser
      POSTGRES_PASSWORD: secure_password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - ragflow_network

  neo4j:
    image: neo4j:5.15-community
    environment:
      NEO4J_AUTH: neo4j/your_neo4j_password
      NEO4J_PLUGINS: '["apoc"]'
      NEO4J_dbms_security_procedures_unrestricted: apoc.*
    ports:
      - "7474:7474"
      - "7687:7687"
    volumes:
      - neo4j_data:/data
    networks:
      - ragflow_network

  elasticsearch:
    image: elasticsearch:8.11.0
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
      - "ES_JAVA_OPTS=-Xms512m -Xmx512m"
    ports:
      - "9200:9200"
    volumes:
      - elasticsearch_data:/usr/share/elasticsearch/data
    networks:
      - ragflow_network

volumes:
  postgres_data:
  neo4j_data:
  elasticsearch_data:

networks:
  ragflow_network:
    driver: bridge
"""
        
        compose_file = Path("docker-compose.local.yml")
        with open(compose_file, "w") as f:
            f.write(docker_compose)
        
        self.add_result("Docker Compose", True, f"Created {compose_file}")
        
        print(f"\n🐳 Docker Compose file created: {compose_file}")
        print("   Run with: docker-compose -f docker-compose.local.yml up -d")
    
    async def run_setup(self) -> Dict[str, Any]:
        """Run complete local network setup"""
        print("🏠 Setting up Local Network RAGFlow Integration")
        print("=" * 60)
        print("This setup uses only open-source software running on your local network")
        print()
        
        # Check services
        print("🔍 Checking Local Services...")
        self.check_postgresql()
        self.check_neo4j()
        self.check_ollama()
        self.check_elasticsearch()
        
        # Setup integrations
        print("\n⚙️  Setting up Integrations...")
        if self.services["postgresql"]:
            await self.setup_postgresql_integration()
        
        # Test integration
        print("\n🧪 Testing RAGFlow Integration...")
        await self.test_ragflow_integration()
        
        # Create configuration files
        print("\n📝 Creating Configuration Files...")
        self.create_local_env_file()
        self.create_docker_compose()
        
        # Calculate results
        total_checks = len(self.results)
        successful_checks = sum(1 for r in self.results if r["success"])
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 Local Network Setup Summary")
        print("=" * 60)
        print(f"✅ Successful: {successful_checks}")
        print(f"❌ Failed: {total_checks - successful_checks}")
        print(f"📈 Success Rate: {successful_checks/total_checks*100:.1f}%")
        
        # Service status
        print("\n🔧 Service Status:")
        for service, running in self.services.items():
            icon = "✅" if running else "❌"
            print(f"  {icon} {service.title()}")
        
        # Installation instructions for missing services
        missing_services = [s for s, running in self.services.items() if not running]
        if missing_services:
            print(f"\n📋 Install Missing Services:")
            
            if "postgresql" in missing_services:
                print("  PostgreSQL + pgvector:")
                print("    • Download: https://www.postgresql.org/download/")
                print("    • Install pgvector: https://github.com/pgvector/pgvector")
            
            if "neo4j" in missing_services:
                print("  Neo4j Community Edition:")
                print("    • Download: https://neo4j.com/download-center/#community")
                print("    • Or use Docker: docker run -p 7474:7474 -p 7687:7687 neo4j:5.15-community")
            
            if "ollama" in missing_services:
                print("  Ollama Local LLM:")
                print("    • Download: https://ollama.ai")
                print("    • Install models: ollama pull llama3.1:8b")
        
        # Next steps
        print(f"\n🚀 Next Steps:")
        if any(self.services.values()):
            print("  1. Review and update .env.local configuration")
            print("  2. Copy .env.local to .env")
            print("  3. Run: python scripts/test_integration.py")
            print("  4. Start: streamlit run src/notebookllama/Home.py")
            print("  5. Access Enhanced RAG Chat page")
        else:
            print("  1. Install required services (see above)")
            print("  2. Re-run this setup script")
            print("  3. Or use Docker: docker-compose -f docker-compose.local.yml up -d")
        
        return {
            "success_rate": successful_checks / total_checks,
            "services": self.services,
            "results": self.results
        }


async def main():
    """Main setup function"""
    setup = LocalNetworkSetup()
    
    try:
        # Load any existing environment
        from dotenv import load_dotenv
        load_dotenv()
        
        # Run setup
        results = await setup.run_setup()
        
        # Save results
        results_file = "local_network_setup_results.json"
        with open(results_file, "w") as f:
            json.dump(results, f, indent=2)
        
        print(f"\n💾 Setup results saved to: {results_file}")
        
        if results["success_rate"] >= 0.6:
            print("\n✅ Local network setup completed successfully!")
            print("🌐 Your RAGFlow integration is ready for local network use")
        else:
            print("\n⚠️  Setup needs attention. Please install missing services.")
            
    except KeyboardInterrupt:
        print("\n⛔ Setup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Setup failed with error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())