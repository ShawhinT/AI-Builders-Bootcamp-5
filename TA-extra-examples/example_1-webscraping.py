# Import required libraries
import os
import json
import asyncio
from typing import List, Optional, Union
from datetime import datetime

# Core libraries
from pydantic import BaseModel, Field, validator, ValidationError
import instructor
import openai

# Web scraping
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from crawl4ai.extraction_strategy import LLMExtractionStrategy
from crawl4ai import LLMConfig

# Set your OpenAI API key (get one from https://platform.openai.com)
OPENAI_API_KEY=os.getenv("OPENAI_API_KEY")

# Step 1: Define our data contract
class Product(BaseModel):
    name: str = Field(..., description="Product name from the webpage")
    price: str = Field(..., description="Current price including currency")
    rating: float = Field(None, description="User rating between 1-5 stars")
    features: list[str] = Field(..., description="Key product features")

# Step 2: Configure the LLM extraction strategy
def create_extraction_strategy():
    return LLMExtractionStrategy(
        llm_config=LLMConfig(
            provider="openai/gpt-4o-mini", 
            api_token=OPENAI_API_KEY
        ),
        schema=Product.model_json_schema(),
        extraction_type="schema",
        instruction="""
            Extract product details from this e-commerce page. 
            Be precise with pricing (include currency symbols).
            If information is not available, use null for optional fields.
            Extract features as a list of key product characteristics.
        """,
        chunk_token_threshold=2048,
        verbose=True
    )

# Step 3: Execute the scraping
async def scrape_product(url: str) -> Optional[Product]:
    """
    Scrape a product page and return structured data
    """
    browser_config = BrowserConfig(
        headless=True,
        verbose=False,
        extra_args=["--disable-gpu", "--no-sandbox"]
    )
    
    crawl_config = CrawlerRunConfig(
        extraction_strategy=create_extraction_strategy(),
        cache_mode=CacheMode.BYPASS,
        word_count_threshold=50
    )
    
    try:
        async with AsyncWebCrawler(config=browser_config) as crawler:
            result = await crawler.arun(url=url, config=crawl_config)
            
            if result.success and result.extracted_content:
                # Parse and validate with Pydantic
                product_data = Product.model_validate_json(result.extracted_content)
                return product_data
            else:
                print(f"Scraping failed: {result.error_message}")
                return None
                
    except ValidationError as e:
        print(f"Data validation failed: {e}")
        print(f"Raw extracted content: {result.extracted_content}")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None
    
async def main():
    product = await scrape_product("https://www.amazon.com/stores/page/A0F96D7A-62B9-40A6-B9FF-6143D9E58BFC")
    if product:
        print(f"Extracted product: {product.model_dump_json(indent=2)}")

if __name__ == "__main__":
    asyncio.run(main())