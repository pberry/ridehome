#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Centralized category definitions for The Ride Home link categorization.

This module contains the single source of truth for all topic categories
used across the codebase (AI categorization, keyword matching, etc.).
"""

# Topic categories - ordered list used for AI categorization
# Order matters: more specific categories first to avoid false matches
TOPIC_CATEGORIES = [
    'Regulation/Policy',
    'Security/Privacy',
    'Crypto/Blockchain',
    'Gaming',
    'Hardware/Chips',
    'AI/Machine Learning',
    'Automotive/Mobility',
    'Streaming/Entertainment',
    'E-commerce/Retail',
    'Social Media',
    'Cloud/Enterprise',
    'FinTech',
    'IPO',
    'Other Tech News'
]


# Topic keywords for keyword-based categorization fallback
# Used when AI categorization is not available
# Order matters: more specific categories first to avoid false matches
TOPIC_KEYWORDS = {
    # Specific tech categories (most specific first)
    'Regulation/Policy': [
        'regulation', 'antitrust', 'ftc', 'sec', 'doj', 'congress', 'senate',
        'lawsuit', 'legal', 'bill', 'legislation', 'policy', 'ban', 'law'
    ],
    'Security/Privacy': [
        'breach', 'hack', 'security', 'privacy', 'encryption', 'vulnerability',
        'cyberattack', 'ransomware', 'malware', 'data breach'
    ],
    'Crypto/Blockchain': [
        'bitcoin', 'crypto', 'blockchain', 'ethereum', 'nft', 'web3', 'defi',
        'coinbase', 'binance', 'solana', 'cryptocurrency'
    ],
    'Gaming': [
        'game', 'gaming', 'riot', 'league of legends', 'xbox', 'playstation',
        'nintendo', 'steam', 'epic games', 'esports', 'twitch'
    ],
    'Hardware/Chips': [
        'chip', 'tpu', 'nvidia', 'amd', 'intel', 'processor', 'gpu', 'cpu',
        'semiconductor', 'tsmc', 'qualcomm', 'arm'
    ],
    'AI/Machine Learning': [
        'ai', 'chatgpt', 'openai', 'gemini', 'claude', 'llm', 'machine learning',
        'neural', 'gpt', 'anthropic', 'midjourney', 'stable diffusion', 'deepmind',
        'copilot', 'artificial intelligence'
    ],
    'Automotive/Mobility': [
        'tesla', 'waymo', 'ev', 'electric vehicle', 'autonomous', 'self-driving',
        'uber', 'lyft', 'cruise', 'rivian', 'ford', 'gm'
    ],
    'Streaming/Entertainment': [
        'netflix', 'spotify', 'youtube', 'streaming', 'disney', 'hulu',
        'paramount', 'warner', 'hbo', 'music', 'video'
    ],
    'E-commerce/Retail': [
        'amazon', 'instacart', 'shopify', 'retail', 'walmart', 'target',
        'e-commerce', 'ecommerce', 'shopping'
    ],
    'Social Media': [
        'facebook', 'meta', 'twitter', 'tiktok', 'instagram', 'snapchat',
        'social media', 'threads', 'bluesky', 'mastodon'
    ],
    'Cloud/Enterprise': [
        'aws', 'azure', 'google cloud', 'enterprise', 'saas', 'salesforce',
        'oracle', 'sap', 'workday', 'cloud computing'
    ],
    'FinTech': [
        'fintech', 'payment', 'paypal', 'stripe', 'square', 'venmo',
        'robinhood', 'banking', 'finance', 'plaid', 'digital wallet'
    ],
    'IPO': [
        'ipo', 'initial public offering', 'going public', 'stock market debut',
        'public listing', 'nasdaq debut', 'nyse listing'
    ],
}
