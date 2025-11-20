def build_lexicon_prompt(theme, mode='keywords'):
    if mode == "keywords":
        prompt = """You are an expert tasked with generating a lexicon of the most important and relevant keywords specific to the {theme}.

Your goal is to compile a list of terms that are critical for understanding and analyzing the {theme}. This lexicon should include only the most essential keywords, phrases, and abbreviations that are directly associated with {theme} topics, analysis, logistics, and industry reporting.

Guidelines:
1. Focus on relevance: Include only the most important and commonly used keywords that are uniquely tied to the {theme}. These should reflect key concepts, industry-specific mechanisms, benchmarks, logistical aspects, and terminology that are central to the theme.
2. Avoid redundancy: Do not repeat the primary terms of the theme in multiple phrases. Include the main term (e.g., "{theme}") only as a standalone term, and focus on other specific terms without redundant repetition.
3. Strict exclusion of generic terms: Exclude any terms that are generic or broadly used across different fields, such as "Arbitrage," "Hedge," "Liquidity," or "Futures Contract," even if they have a specific meaning within the context of {theme}. Only include terms that are uniquely relevant to {theme} and cannot be applied broadly.
4. Include specific variations: Where applicable, provide both the full form and common abbreviations relevant to the {theme}. Present the full term and its abbreviation as separate entries. For example, instead of "Zero Lower Bound (ZLB)", list "Zero Lower Bound" and "ZLB" as separate keywords.
5. Ensure clarity: Each keyword should be concise, clear, and directly relevant to the {theme}, avoiding any ambiguity.
6. Select only the most critical: There is no need to reach a specific number of keywords. Focus solely on the most crucial terms without padding the list. If fewer keywords meet the criteria, that is acceptable.

The output should be a lexicon of only the most critical and uniquely relevant keywords related to the {theme}, formatted as a JSON list, accessible with the key {mode}, with full terms and abbreviations listed separately.
"""
    else:
        prompt = """You are an expert tasked with generating a lexicon of the most important and relevant sentences specific to the {theme}.

Your goal is to compile a list of concise, informative sentences that are critical for understanding and analyzing the {theme}. Each sentence should capture a unique aspect, mechanism, or implication of the theme.

Guidelines:
1. Focus on relevance: Include only the most important and commonly discussed sentences that are uniquely tied to the {theme}. These should reflect key concepts, industry-specific mechanisms, benchmarks, logistical aspects, and terminology that are central to the theme.
2. Avoid redundancy: Do not repeat the primary terms of the theme in multiple sentences. Include the main term (e.g., "{theme}") only as a standalone sentence, and focus on other specific sentences without redundant repetition.
3. Strict exclusion of generic sentences: Exclude any sentences that are generic or broadly used across different fields, even if they have a specific meaning within the context of {theme}. Only include sentences that are uniquely relevant to {theme} and cannot be applied broadly.
4. Include specific variations: Where applicable, provide both the full form and common abbreviations relevant to the {theme}. Present the full sentence and its abbreviation as separate entries.
5. Ensure clarity: Each sentence should be concise, clear, and directly relevant to the {theme}, avoiding any ambiguity.
6. Select only the most critical: There is no need to reach a specific number of sentences. Focus solely on the most crucial sentences without padding the list. If fewer sentences meet the criteria, that is acceptable.

The output should be a lexicon of only the most critical and uniquely relevant sentences related to the {theme}, formatted as a JSON list, accessible with the key {mode}, with full sentences.
"""
    return prompt.strip().format(theme=theme, mode=mode)