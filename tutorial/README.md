# Bigdata Research Tools - Interactive Tutorial

Welcome to the hands-on tutorial for the Bigdata Research Tools library! This interactive Jupyter notebook demonstrates all key functionality with practical, working examples.

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- Bigdata.com API credentials
- [uv](https://github.com/astral-sh/uv) (recommended) or pip

### Setup with uv (Recommended)

1. **Navigate to tutorial directory:**
   ```bash
   cd tutorial
   ```

2. **Create virtual environment and install dependencies:**
   ```bash
   uv venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   uv pip install -r requirements.txt
   uv pip install -e ../.
   ```

3. **Set up authentication:**
   ```bash
   # Create .env file with your credentials
   echo "BIGDATA_API_KEY=your_api_key_here" > .env
   echo "BIGDATA_API_BASE_URL=your_base_url_here" >> .env
   ```

4. **Launch Jupyter:**
   ```bash
   jupyter lab tutorial_notebook.ipynb
   ```

### Alternative Setup with pip

```bash
python -m venv tutorial_env
source tutorial_env/bin/activate  # On Windows: tutorial_env\Scripts\activate
pip install -r requirements.txt
pip install -e ..
jupyter lab tutorial_notebook.ipynb
```

## 📚 What You'll Learn

The tutorial covers:

- **🔑 Authentication Setup** - Connect to the Bigdata.com API
- **🔍 Basic Searches** - Search by companies and custom queries
- **📊 Data Processing** - Work with search results and DataFrames
- **💡 Best Practices** - Optimize searches and handle results efficiently

## 🎯 Tutorial Structure

1. **Setup and Authentication** - Import libraries and connect to API
2. **Search by Companies** - Find documents mentioning specific companies
3. **Custom Query Search** - Build and execute advanced search queries
4. **Next Steps** - Explore advanced workflows and examples

## ⚠️ Important Notes

- **Run cells in order** - Each cell depends on previous ones
- **API credentials required** - Create a `.env` file with your Bigdata.com credentials
- **Sample data** - The tutorial uses real API calls with sample companies

## 🔗 Next Steps

After completing this tutorial:

1. **Explore Advanced Workflows:**
   - NarrativeMiner - Track narrative evolution
   - ThematicScreener - Analyze theme exposure
   - RiskAnalyzer - Assess risk factors

2. **Run Complete Examples:** Check out the `../examples/` directory

3. **Build Custom Workflows:** Use the [Bigdata Cookbook](https://github.com/Bigdata-com/bigdata-cookbook) for more examples

## 🆘 Troubleshooting

- **Import errors?** Make sure you installed the package: `pip install -e ../.`
- **Authentication issues?** Verify your `.env` file has correct credentials
- **No results?** Try different date ranges or search terms

## 📖 Documentation

For comprehensive documentation, see the [USER_GUIDE.md](../README.md) in the parent directory.
