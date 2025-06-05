import pandas as pd
import numpy as np
from enum import Enum, auto
import warnings

class WeightMethod(Enum):
    EQUAL = auto()      # Equal weighting for all companies
    COLUMN = auto()     # Weight based on a specific column (e.g., market cap)
    SCORE = auto()      # Weight based on score values (softmax-normalized)
    
    def __str__(self):
        return self.name.lower()


class PortfolioConstructor:
    """
    A class to construct balanced and weighted portfolios with constraints.
    
    This class provides methods to create portfolios with balanced category representation,
    flexible weighting methods, and customizable position and category weight constraints.
    Includes safeguards against infinite loops in constraint enforcement.
    """
    
    def __init__(
        self,
        max_iterations: int = 1000,
        tolerance: float = 1e-6
    ) -> None:
        """
        Initialize the PortfolioConstructor with constraint enforcement parameters.
        
        Parameters:
        -----------
        max_iterations : int, default=1000
            Maximum iterations for constraint enforcement
        tolerance : float, default=1e-6
            Convergence tolerance for constraint enforcement
        """
        self.max_iterations = max_iterations
        self.tolerance = tolerance
    
    def construct_portfolio(
        self,
        df: pd.DataFrame,
        score_col: str,
        balance_col: str,
        weight_col: str = None,
        size: int = None,
        max_position_weight: float = 0.05,
        max_category_weight: float = 0.15,
        weight_method: WeightMethod = WeightMethod.EQUAL
    ) -> pd.DataFrame:
        """
        Build a balanced and weighted portfolio with position and category constraints.
        
        This method performs three main steps:
        1. Balances the portfolio by selecting top companies from each category
        2. Calculates initial weights based on the selected weighting method
        3. Enforces position and category weight constraints with convergence protection
        
        Parameters:
        -----------
        df : pandas.DataFrame
            DataFrame containing company data
        score_col : str
            Column name to use for ranking companies within each category
        balance_col : str
            Column name to use for balancing (e.g., 'sector', 'industry', 'region')
        weight_col : str, optional
            Column name to use for weighting when using COLUMN or SCORE methods
        size : int, optional
            Target number of companies in the portfolio. Defaults to number of unique categories
        max_position_weight : float, default=0.05
            Maximum weight allowed for any single position (e.g., 0.05 = 5%)
        max_category_weight : float, default=0.15
            Maximum weight allowed for any category (e.g., 0.15 = 15%)
        weight_method : WeightMethod, default=WeightMethod.EQUAL
            Weighting methodology to use
            
        Returns:
        --------
        pandas.DataFrame
            Portfolio with calculated weights, sorted by weight (descending)
        """
        df = df.copy()
        categories = df[balance_col].unique()
        n_categories = len(categories)
        if size is None or size < n_categories:
            size = n_categories

        # Step 1: Select top companies per category (balancing)
        portfolio = self._balance_by_category(df, score_col, balance_col, size)

        # Step 2: Calculate raw weights based on selected method
        portfolio = self._calculate_weights(portfolio, weight_method, weight_col)

        # Step 3: Enforce position and category weight constraints with safety checks
        portfolio = self._enforce_constraints(portfolio, max_position_weight, max_category_weight, balance_col)

        # Clean up temporary columns and sort by weight
        portfolio = portfolio.drop(columns=["rank", "raw_weight"])
        return portfolio.sort_values("weight", ascending=False)
    
    def _balance_by_category(self, df: pd.DataFrame, score_col: str, balance_col: str, size: int) -> pd.DataFrame:
        """
        Select top companies from each category to create a balanced portfolio.
        
        Parameters:
        -----------
        df : pandas.DataFrame
            DataFrame containing company data
        score_col : str
            Column to use for ranking within categories
        balance_col : str
            Column to use for category balancing
        size : int
            Target portfolio size
            
        Returns:
        --------
        pandas.DataFrame
            Balanced subset of companies
        """
        categories = df[balance_col].unique()
        n_categories = len(categories)
        
        # Calculate allocations per category
        base_per_category = size // n_categories
        extras = size % n_categories
        allocations = pd.Series(base_per_category, index=categories)
        
        # Distribute extras to categories that have enough companies
        category_sizes = df.groupby(balance_col).size()
        eligible = category_sizes[category_sizes > base_per_category].index
        if extras > 0 and len(eligible) > 0:
            allocations.loc[eligible[:extras]] += 1

        # Rank and select top companies per category
        df = df.copy()
        df["rank"] = df.groupby(balance_col)[score_col].rank(ascending=False, method="first")
        mask = df.apply(lambda x: x["rank"] <= allocations.get(x[balance_col], 0), axis=1)
        
        return df[mask].copy()
    
    def _calculate_weights(self, portfolio: pd.DataFrame, weight_method: WeightMethod, weight_col: str) -> pd.DataFrame:
        """
        Calculate initial weights based on the specified weighting method.
        
        Parameters:
        -----------
        portfolio : pandas.DataFrame
            DataFrame of selected companies
        weight_method : WeightMethod
            Method to use for calculating weights
        weight_col : str or None
            Column to use for column-based or score-based weighting
            
        Returns:
        --------
        pandas.DataFrame
            Portfolio with added 'weight' column
        """
        portfolio = portfolio.copy()
        
        # Calculate raw weights based on selected method
        if weight_method == WeightMethod.EQUAL or weight_col is None:
            # Equal weighting - all positions get the same raw weight
            portfolio["raw_weight"] = 1.0
        elif weight_method == WeightMethod.COLUMN:
            # Column-based weighting (e.g., market cap)
            vals = portfolio[weight_col].abs()
            portfolio["raw_weight"] = vals
        elif weight_method == WeightMethod.SCORE:
            # Score-based weighting using softmax normalization
            scores = portfolio[weight_col].values
            # More stable softmax with clipping to prevent extreme values
            scores_clipped = np.clip(scores, -50, 50)  # Prevent overflow
            exp_scores = np.exp(scores_clipped - np.max(scores_clipped))
            portfolio["raw_weight"] = exp_scores
        else:
            raise ValueError(f"Unsupported weight_method: {weight_method}")

        # Normalize raw weights to sum to 1
        portfolio["weight"] = portfolio["raw_weight"] / portfolio["raw_weight"].sum()
        
        return portfolio
    
    def _enforce_constraints(self, df: pd.DataFrame, max_pos: float, max_cat: float, balance_col: str) -> pd.DataFrame:
        """
        Enforce maximum position weight and category weight constraints.
        
        Includes convergence protection to prevent infinite loops.
        
        Parameters:
        -----------
        df : pandas.DataFrame
            Portfolio DataFrame with initial weights
        max_pos : float
            Maximum allowed weight for any single position (0-1)
        max_cat : float
            Maximum allowed weight for any category (0-1)
        balance_col : str
            Column name for category grouping
            
        Returns:
        --------
        pandas.DataFrame
            Portfolio with weights adjusted to meet all constraints
        """
        df = df.copy()
        
        # Validation checks
        if max_pos <= 0 or max_pos > 1:
            raise ValueError(f"max_position_weight must be between 0 and 1, got {max_pos}")
        if max_cat <= 0 or max_cat > 1:
            raise ValueError(f"max_category_weight must be between 0 and 1, got {max_cat}")
        
        # Check if constraints are achievable
        n_positions = len(df)
        n_categories = df[balance_col].nunique()
        
        # Warn if constraints might be too tight
        if max_pos * n_positions < 1.0:
            warnings.warn(f"Position constraint may be too tight: {max_pos:.1%} * {n_positions} positions = {max_pos * n_positions:.1%} total")
        
        if max_cat * n_categories < 1.0:
            warnings.warn(f"Category constraint may be too tight: {max_cat:.1%} * {n_categories} categories = {max_cat * n_categories:.1%} total")
        
        iteration = 0
        prev_weights = None
        
        while iteration < self.max_iterations:
            iteration += 1
            
            # Track whether we made any changes
            position_violation = False
            category_violation = False
            
            # Check and fix position weight violations
            overweight_positions = df['weight'] > max_pos
            if overweight_positions.any():
                position_violation = True
                
                # Calculate total excess weight from violating positions
                excess = (df.loc[overweight_positions, 'weight'] - max_pos).sum()
                
                # Cap violating positions
                df.loc[overweight_positions, 'weight'] = max_pos
                
                # Redistribute excess to compliant positions proportionally
                compliant = ~overweight_positions
                if compliant.any() and df.loc[compliant, 'weight'].sum() > 0:
                    df.loc[compliant, 'weight'] += excess * (
                        df.loc[compliant, 'weight'] / df.loc[compliant, 'weight'].sum()
                    )
            
            # Check and fix category weight violations
            category_weights = df.groupby(balance_col)['weight'].sum()
            overweight_categories = category_weights > max_cat
            
            if overweight_categories.any():
                category_violation = True
                
                # Scale down weights in overweight categories
                for category in category_weights[overweight_categories].index:
                    mask = df[balance_col] == category
                    current_weight = df.loc[mask, 'weight'].sum()
                    
                    if current_weight > 0:  # Avoid division by zero
                        # Scale all category holdings proportionally
                        scale_factor = max_cat / current_weight
                        df.loc[mask, 'weight'] *= scale_factor
                
                # Renormalize all weights to sum to 1
                total_weight = df['weight'].sum()
                if total_weight > 0:
                    df['weight'] = df['weight'] / total_weight
            
            # Check for convergence
            if not position_violation and not category_violation:
                break
                
            # Check if weights have converged (small changes)
            if prev_weights is not None:
                weight_change = np.abs(df['weight'].values - prev_weights).max()
                if weight_change < self.tolerance:
                    warnings.warn(f"Constraint enforcement converged with tolerance {self.tolerance:.2e} after {iteration} iterations")
                    break
            
            prev_weights = df['weight'].values.copy()
        
        if iteration >= self.max_iterations:
            warnings.warn(f"Constraint enforcement stopped after {self.max_iterations} iterations without full convergence")
        
        return df