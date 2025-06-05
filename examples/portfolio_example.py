import pandas as pd
import numpy as np
import logging
from bigdata_research_tools.portfolio.portfolio_constructor import PortfolioConstructor, WeightMethod

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_sample_data():
    """Create sample data for demonstration purposes."""
    np.random.seed(42)  # For reproducible results
    
    # Define sample sectors, industries, and countries
    sectors = ['Technology', 'Healthcare', 'Financial Services', 'Consumer Goods', 'Energy']
    industries = ['Software', 'Pharmaceuticals', 'Banking', 'Retail', 'Oil & Gas', 
                 'Semiconductors', 'Biotechnology', 'Insurance', 'Automotive', 'Utilities']
    countries = ['USA', 'Germany', 'Japan', 'UK', 'Canada', 'France', 'Australia']
    
    # Generate 100 sample companies
    n_companies = 100
    data = {
        'Company': [f'Company_{i:03d}' for i in range(1, n_companies + 1)],
        'Sector': np.random.choice(sectors, n_companies),
        'Industry': np.random.choice(industries, n_companies),
        'Country': np.random.choice(countries, n_companies),
        'Market Cap (B)': np.random.lognormal(mean=2, sigma=1.5, size=n_companies),
        'Composite Score': np.random.normal(loc=75, scale=15, size=n_companies),
        'ESG Score': np.random.uniform(20, 95, n_companies),
        'Revenue Growth': np.random.normal(loc=8, scale=12, size=n_companies)
    }
    
    df = pd.DataFrame(data)
    
    # Ensure scores are reasonable
    df['Composite Score'] = np.clip(df['Composite Score'], 0, 100)
    df['ESG Score'] = np.round(df['ESG Score'], 1)
    df['Market Cap (B)'] = np.round(df['Market Cap (B)'], 2)
    df['Revenue Growth'] = np.round(df['Revenue Growth'], 1)
    
    return df

def example_1_basic_equal_weighted():
    """Example 1: Basic equal-weighted portfolio balanced by sector."""
    logger.info("=" * 60)
    logger.info("EXAMPLE 1: Basic Equal-Weighted Portfolio (Sector Balanced)")
    logger.info("=" * 60)
    
    # Create sample data
    df = create_sample_data()
    
    # Initialize portfolio constructor (only technical parameters)
    constructor = PortfolioConstructor(
        max_iterations=1000,
        tolerance=1e-6
    )
    
    # Construct portfolio with constraints specified in method call
    portfolio = constructor.construct_portfolio(
        df=df,
        score_col="Composite Score",
        balance_col="Sector",
        size=20,
        max_position_weight=0.08,  # 8% max per position
        max_category_weight=0.25,  # 25% max per sector
        weight_method=WeightMethod.EQUAL
    )
    
    logger.info(f"Portfolio Size: {len(portfolio)} companies")
    logger.info(f"Sectors Represented: {portfolio['Sector'].nunique()}")
    logger.info("\nTop 10 Holdings:")
    logger.info(f"\n{portfolio[['Company', 'Sector', 'Composite Score', 'weight']].head(10).to_string(index=False)}")
    
    logger.info(f"\nSector Allocation:")
    sector_weights = portfolio.groupby('Sector')['weight'].sum().sort_values(ascending=False)
    for sector, weight in sector_weights.items():
        logger.info(f"  {sector}: {weight:.1%}")
    
    logger.info(f"\nWeight Statistics:")
    logger.info(f"  Min Weight: {portfolio['weight'].min():.1%}")
    logger.info(f"  Max Weight: {portfolio['weight'].max():.1%}")
    logger.info(f"  Mean Weight: {portfolio['weight'].mean():.1%}")
    logger.info(f"  Total Weight: {portfolio['weight'].sum():.1%}")

def example_2_market_cap_weighted():
    """Example 2: Market cap weighted portfolio balanced by country."""
    logger.info("\n" + "=" * 60)
    logger.info("EXAMPLE 2: Market Cap Weighted Portfolio (Country Balanced)")
    logger.info("=" * 60)
    
    # Create sample data
    df = create_sample_data()
    
    # Initialize constructor
    constructor = PortfolioConstructor()
    
    # Construct portfolio with market cap weighting
    portfolio = constructor.construct_portfolio(
        df=df,
        score_col="Composite Score",
        balance_col="Country",
        weight_col="Market Cap (B)",  # Use market cap for weighting
        size=20,
        max_position_weight=0.10,  # 10% max per position (more relaxed)
        max_category_weight=0.40,  # 40% max per country (more relaxed)
        weight_method=WeightMethod.COLUMN
    )
    
    logger.info(f"Portfolio Size: {len(portfolio)} companies")
    logger.info(f"Countries Represented: {portfolio['Country'].nunique()}")
    logger.info("\nTop 10 Holdings:")
    display_cols = ['Company', 'Country', 'Market Cap (B)', 'Composite Score', 'weight']
    logger.info(f"\n{portfolio[display_cols].head(10).to_string(index=False)}")
    
    logger.info(f"\nCountry Allocation:")
    country_weights = portfolio.groupby('Country')['weight'].sum().sort_values(ascending=False)
    for country, weight in country_weights.items():
        logger.info(f"  {country}: {weight:.1%}")

def example_3_score_weighted():
    """Example 3: Score-weighted portfolio using softmax normalization."""
    logger.info("\n" + "=" * 60)
    logger.info("EXAMPLE 3: Score-Weighted Portfolio (ESG Score, Industry Balanced)")
    logger.info("=" * 60)
    
    # Create sample data
    df = create_sample_data()
    
    # Initialize constructor
    constructor = PortfolioConstructor()
    
    # Construct portfolio using ESG Score for weighting
    portfolio = constructor.construct_portfolio(
        df=df,
        score_col="Composite Score",
        balance_col="Industry",
        weight_col="ESG Score",  # Use ESG score for softmax weighting
        size=25,  # Larger portfolio
        max_position_weight=0.07,  # 7% max per position
        max_category_weight=0.20,  # 20% max per industry
        weight_method=WeightMethod.SCORE
    )
    
    logger.info(f"Portfolio Size: {len(portfolio)} companies")
    logger.info(f"Industries Represented: {portfolio['Industry'].nunique()}")
    logger.info("\nTop 10 Holdings:")
    display_cols = ['Company', 'Industry', 'ESG Score', 'Composite Score', 'weight']
    logger.info(f"\n{portfolio[display_cols].head(10).to_string(index=False)}")
    
    logger.info(f"\nIndustry Allocation:")
    industry_weights = portfolio.groupby('Industry')['weight'].sum().sort_values(ascending=False)
    for industry, weight in industry_weights.items():
        logger.info(f"  {industry}: {weight:.1%}")

def example_4_custom_constraints():
    """Example 4: Custom constraints demonstration."""
    logger.info("\n" + "=" * 60)
    logger.info("EXAMPLE 4: Custom Constraints Demonstration")
    logger.info("=" * 60)
    
    # Create sample data
    df = create_sample_data()
    
    # Initialize constructor with custom technical parameters
    constructor = PortfolioConstructor(
        max_iterations=2000,  # More iterations for complex constraints
        tolerance=1e-8       # Tighter tolerance
    )
    
    # Construct portfolio with tight constraints
    portfolio = constructor.construct_portfolio(
        df=df,
        score_col="Composite Score",
        balance_col="Sector",
        weight_col="Market Cap (B)",
        size=15,
        max_position_weight=0.04,  # Very tight: 4% max per position
        max_category_weight=0.15,  # Tight: 15% max per sector
        weight_method=WeightMethod.COLUMN
    )
    
    logger.info(f"Portfolio Size: {len(portfolio)} companies")
    logger.info("\nAll Holdings:")
    display_cols = ['Company', 'Sector', 'Market Cap (B)', 'Composite Score', 'weight']
    logger.info(f"\n{portfolio[display_cols].to_string(index=False)}")
    
    logger.info(f"\nConstraint Verification:")
    logger.info(f"  Max Position Weight: {portfolio['weight'].max():.1%} (limit: 4.0%)")
    sector_max = portfolio.groupby('Sector')['weight'].sum().max()
    logger.info(f"  Max Sector Weight: {sector_max:.1%} (limit: 15.0%)")

def example_5_comparison():
    """Example 5: Compare different weighting methods side by side."""
    logger.info("\n" + "=" * 60)
    logger.info("EXAMPLE 5: Weighting Method Comparison")
    logger.info("=" * 60)
    
    # Create sample data
    df = create_sample_data()
    
    # Initialize constructor
    constructor = PortfolioConstructor()
    
    methods = [
        (WeightMethod.EQUAL, None, "Equal Weight"),
        (WeightMethod.COLUMN, "Market Cap (B)", "Market Cap Weight"),
        (WeightMethod.SCORE, "Composite Score", "Score Weight (Softmax)")
    ]
    
    for weight_method, weight_col, description in methods:
        logger.info(f"\n{description}:")
        logger.info("-" * 40)
        
        portfolio = constructor.construct_portfolio(
            df=df,
            score_col="Composite Score",
            balance_col="Sector",
            weight_col=weight_col,
            size=15,
            max_position_weight=0.06,
            max_category_weight=0.25,
            weight_method=weight_method
        )
        
        logger.info(f"Top 5 Holdings:")
        display_cols = ['Company', 'Sector', 'weight']
        if weight_col:
            display_cols.insert(2, weight_col)
        logger.info(f"\n{portfolio[display_cols].head(5).to_string(index=False)}")
        
        logger.info(f"Weight Range: {portfolio['weight'].min():.1%} - {portfolio['weight'].max():.1%}")

def main():
    """Run all examples."""
    logger.info("Starting Portfolio Constructor Examples")
    
    # Run all examples
    example_1_basic_equal_weighted()
    example_2_market_cap_weighted()
    example_3_score_weighted()
    example_4_custom_constraints()
    example_5_comparison()
    
    logger.info("\n" + "=" * 60)
    logger.info("Examples completed successfully!")
    logger.info("=" * 60)

if __name__ == "__main__":
    main()