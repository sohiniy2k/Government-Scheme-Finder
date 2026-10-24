"""Constants for Phase 1 Data Processing and Phase 2 Matching reuse."""

# 36 States and Union Territories of India
STATES_AND_UTS = [
    # 28 States
    "Andhra Pradesh",
    "Arunachal Pradesh",
    "Assam",
    "Bihar",
    "Chhattisgarh",
    "Goa",
    "Gujarat",
    "Haryana",
    "Himachal Pradesh",
    "Jharkhand",
    "Karnataka",
    "Kerala",
    "Madhya Pradesh",
    "Maharashtra",
    "Manipur",
    "Meghalaya",
    "Mizoram",
    "Nagaland",
    "Odisha",
    "Punjab",
    "Rajasthan",
    "Sikkim",
    "Tamil Nadu",
    "Telangana",
    "Tripura",
    "Uttar Pradesh",
    "Uttarakhand",
    "West Bengal",
    # 8 Union Territories
    "Andaman and Nicobar Islands",
    "Chandigarh",
    "Dadra and Nagar Haveli and Daman and Diu",
    "Delhi",
    "Jammu and Kashmir",
    "Ladakh",
    "Lakshadweep",
    "Puducherry",
]

# Standard occupations list saved for Phase 2 reuse
OCCUPATIONS = [
    "student",
    "farmer",
    "fisherman",
    "artisan",
    "construction_worker",
    "entrepreneur",
    "unemployed",
    "senior_citizen",
    "any",
]

# 19 Official Scheme Categories
SCHEME_CATEGORIES = [
    "Agriculture",
    "Banking",
    "Business & Entrepreneurship",
    "Education & Learning",
    "Financial Services and Insurance",
    "Health & Wellness",
    "Housing & Shelter",
    "IT & Communications",
    "Law & Justice",
    "Public Safety",
    "Rural & Environment",
    "Science",
    "Skills & Employment",
    "Social welfare & Empowerment",
    "Sports & Culture",
    "Transport & Infrastructure",
    "Travel & Tourism",
    "Utility & Sanitation",
    "Women and Child",
]

# State detection patterns with word boundary protection:
# (pattern, canonical_name)
# Multi-word and aliases are placed before shorter substrings.
STATE_PATTERNS = [
    # Dadra & Nagar Haveli and Daman & Diu
    (r'(?<!\w)dadra\s+and\s+nagar\s+haveli\s+and\s+daman\s+and\s+diu(?!\w)', "Dadra and Nagar Haveli and Daman and Diu"),
    (r'(?<!\w)dadra\s+and\s+nagar\s+haveli(?!\w)', "Dadra and Nagar Haveli and Daman and Diu"),
    (r'(?<!\w)daman\s+and\s+diu(?!\w)', "Dadra and Nagar Haveli and Daman and Diu"),
    (r'(?<!\w)dadra(?!\w)', "Dadra and Nagar Haveli and Daman and Diu"),
    (r'(?<!\w)daman(?!\w)', "Dadra and Nagar Haveli and Daman and Diu"),

    # Jammu & Kashmir
    (r'(?<!\w)jammu\s+(?:and|&)\s+kashmir(?!\w)', "Jammu and Kashmir"),
    (r'(?<!\w)j\s*&\s*k(?!\w)', "Jammu and Kashmir"),
    (r'(?<!\w)jammu(?!\w)', "Jammu and Kashmir"),
    (r'(?<!\w)kashmir(?!\w)', "Jammu and Kashmir"),

    # Andaman & Nicobar Islands
    (r'(?<!\w)andaman\s+(?:and|&)\s+nicobar(?:\s+islands)?(?!\w)', "Andaman and Nicobar Islands"),

    # States & other UTs
    (r'(?<!\w)andhra\s+pradesh(?!\w)', "Andhra Pradesh"),
    (r'(?<!\w)arunachal\s+pradesh(?!\w)', "Arunachal Pradesh"),
    (r'(?<!\w)assam(?!\w)', "Assam"),
    (r'(?<!\w)bihar(?!\w)', "Bihar"),
    (r'(?<!\w)chandigarh(?!\w)', "Chandigarh"),
    (r'(?<!\w)chhattisgarh(?!\w)', "Chhattisgarh"),
    (r'(?<!\w)nct\s+of\s+delhi(?!\w)', "Delhi"),
    (r'(?<!\w)delhi(?!\w)', "Delhi"),
    (r'(?<!\w)goa(?!\w)', "Goa"),
    (r'(?<!\w)gujarat(?!\w)', "Gujarat"),
    (r'(?<!\w)haryana(?!\w)', "Haryana"),
    (r'(?<!\w)himachal\s+pradesh(?!\w)', "Himachal Pradesh"),
    (r'(?<!\w)jharkhand(?!\w)', "Jharkhand"),
    (r'(?<!\w)karnataka(?!\w)', "Karnataka"),
    (r'(?<!\w)kerala(?!\w)', "Kerala"),
    (r'(?<!\w)ladakh(?!\w)', "Ladakh"),
    (r'(?<!\w)lakshadweep(?!\w)', "Lakshadweep"),
    (r'(?<!\w)madhya\s+pradesh(?!\w)', "Madhya Pradesh"),
    (r'(?<!\w)maharashtra(?!\w)', "Maharashtra"),
    (r'(?<!\w)manipur(?!\w)', "Manipur"),
    (r'(?<!\w)meghalaya(?!\w)', "Meghalaya"),
    (r'(?<!\w)mizoram(?!\w)', "Mizoram"),
    (r'(?<!\w)nagaland(?!\w)', "Nagaland"),
    (r'(?<!\w)odisha(?!\w)', "Odisha"),
    (r'(?<!\w)orissa(?!\w)', "Odisha"),
    (r'(?<!\w)puducherry(?!\w)', "Puducherry"),
    (r'(?<!\w)pondicherry(?!\w)', "Puducherry"),
    (r'(?<!\w)punjab(?!\w)', "Punjab"),
    (r'(?<!\w)rajasthan(?!\w)', "Rajasthan"),
    (r'(?<!\w)sikkim(?!\w)', "Sikkim"),
    (r'(?<!\w)tamil\s+nadu(?!\w)', "Tamil Nadu"),
    (r'(?<!\w)telangana(?!\w)', "Telangana"),
    (r'(?<!\w)tripura(?!\w)', "Tripura"),
    (r'(?<!\w)uttar\s+pradesh(?!\w)', "Uttar Pradesh"),
    (r'(?<!\w)uttarakhand(?!\w)', "Uttarakhand"),
    (r'(?<!\w)uttaranchal(?!\w)', "Uttarakhand"),
    (r'(?<!\w)west\s+bengal(?!\w)', "West Bengal"),
]
