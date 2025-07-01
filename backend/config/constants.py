"""
Application constants and configuration data.
"""

# Enhanced Policy Areas Configuration
POLICY_AREAS = [
    {
        "id": "ai-safety",
        "name": "AI Safety",
        "description": "Policies ensuring AI systems are safe and beneficial",
        "icon": "🛡️",
        "color": "from-red-500 to-pink-600",
        "gradient": "bg-gradient-to-r from-red-500 to-pink-600"
    },
    {
        "id": "cyber-safety",
        "name": "CyberSafety", 
        "description": "Cybersecurity and digital safety policies",
        "icon": "🔒",
        "color": "from-blue-500 to-cyan-600",
        "gradient": "bg-gradient-to-r from-blue-500 to-cyan-600"
    },
    {
        "id": "digital-education",
        "name": "Digital Education",
        "description": "Educational technology and digital literacy policies",
        "icon": "🎓",
        "color": "from-green-500 to-emerald-600",
        "gradient": "bg-gradient-to-r from-green-500 to-emerald-600"
    },
    {
        "id": "digital-inclusion",
        "name": "Digital Inclusion",
        "description": "Bridging the digital divide and ensuring equal access",
        "icon": "🌐",
        "color": "from-purple-500 to-indigo-600",
        "gradient": "bg-gradient-to-r from-purple-500 to-indigo-600"
    },
    {
        "id": "digital-leisure",
        "name": "Digital Leisure",
        "description": "Gaming, entertainment, and digital recreation policies",
        "icon": "🎮",
        "color": "from-yellow-500 to-orange-600",
        "gradient": "bg-gradient-to-r from-yellow-500 to-orange-600"
    },
    {
        "id": "disinformation",
        "name": "(Dis)Information",
        "description": "Combating misinformation and promoting truth",
        "icon": "📰",
        "color": "from-gray-500 to-slate-600",
        "gradient": "bg-gradient-to-r from-gray-500 to-slate-600"
    },
    {
        "id": "digital-work",
        "name": "Digital Work",
        "description": "Future of work and digital employment policies",
        "icon": "💼",
        "color": "from-teal-500 to-blue-600",
        "gradient": "bg-gradient-to-r from-teal-500 to-blue-600"
    },
    {
        "id": "mental-health",
        "name": "Mental Health",
        "description": "Digital wellness and mental health policies",
        "icon": "🧠",
        "color": "from-pink-500 to-rose-600",
        "gradient": "bg-gradient-to-r from-pink-500 to-rose-600"
    },
    {
        "id": "physical-health",
        "name": "Physical Health",
        "description": "Healthcare technology and physical wellness policies",
        "icon": "❤️",
        "color": "from-emerald-500 to-green-600",
        "gradient": "bg-gradient-to-r from-emerald-500 to-green-600"
    },
    {
        "id": "social-media-gaming",
        "name": "Social Media/Gaming Regulation",
        "description": "Social media platforms and gaming regulation",
        "icon": "📱",
        "color": "from-indigo-500 to-purple-600",
        "gradient": "bg-gradient-to-r from-indigo-500 to-purple-600"
    }
]

# Countries list
COUNTRIES = [
    "Afghanistan", "Albania", "Algeria", "Andorra", "Angola", "Antigua and Barbuda",
    "Argentina", "Armenia", "Australia", "Austria", "Azerbaijan", "Bahamas",
    "Bahrain", "Bangladesh", "Barbados", "Belarus", "Belgium", "Belize",
    "Benin", "Bhutan", "Bolivia", "Bosnia and Herzegovina", "Botswana", "Brazil",
    "Brunei", "Bulgaria", "Burkina Faso", "Burundi", "Cambodia", "Cameroon",
    "Canada", "Cape Verde", "Central African Republic", "Chad", "Chile", "China",
    "Colombia", "Comoros", "Congo", "Costa Rica", "Croatia", "Cuba",
    "Cyprus", "Czech Republic", "Denmark", "Djibouti", "Dominica", "Dominican Republic",
    "Ecuador", "Egypt", "El Salvador", "Equatorial Guinea", "Eritrea", "Estonia",
    "Ethiopia", "Fiji", "Finland", "France", "Gabon", "Gambia",
    "Georgia", "Germany", "Ghana", "Greece", "Grenada", "Guatemala",
    "Guinea", "Guinea-Bissau", "Guyana", "Haiti", "Honduras", "Hungary",
    "Iceland", "India", "Indonesia", "Iran", "Iraq", "Ireland",
    "Israel", "Italy", "Jamaica", "Japan", "Jordan", "Kazakhstan",
    "Kenya", "Kiribati", "North Korea", "South Korea", "Kuwait", "Kyrgyzstan",
    "Laos", "Latvia", "Lebanon", "Lesotho", "Liberia", "Libya",
    "Liechtenstein", "Lithuania", "Luxembourg", "Macedonia", "Madagascar", "Malawi",
    "Malaysia", "Maldives", "Mali", "Malta", "Marshall Islands", "Mauritania",
    "Mauritius", "Mexico", "Micronesia", "Moldova", "Monaco", "Mongolia",
    "Montenegro", "Morocco", "Mozambique", "Myanmar", "Namibia", "Nauru",
    "Nepal", "Netherlands", "New Zealand", "Nicaragua", "Niger", "Nigeria",
    "Norway", "Oman", "Pakistan", "Palau", "Panama", "Papua New Guinea",
    "Paraguay", "Peru", "Philippines", "Poland", "Portugal", "Qatar",
    "Romania", "Russia", "Rwanda", "Saint Kitts and Nevis", "Saint Lucia", "Saint Vincent and the Grenadines",
    "Samoa", "San Marino", "Sao Tome and Principe", "Saudi Arabia", "Senegal", "Serbia",
    "Seychelles", "Sierra Leone", "Singapore", "Slovakia", "Slovenia", "Solomon Islands",
    "Somalia", "South Africa", "South Sudan", "Spain", "Sri Lanka", "Sudan",
    "Suriname", "Swaziland", "Sweden", "Switzerland", "Syria", "Taiwan",
    "Tajikistan", "Tanzania", "Thailand", "Timor-Leste", "Togo", "Tonga",
    "Trinidad and Tobago", "Tunisia", "Turkey", "Turkmenistan", "Tuvalu", "Uganda",
    "Ukraine", "United Arab Emirates", "United Kingdom", "United States", "Uruguay", "Uzbekistan",
    "Vanuatu", "Vatican City", "Venezuela", "Vietnam", "Yemen", "Zambia", "Zimbabwe"
]

# Policy status options
POLICY_STATUSES = ['pending', 'approved', 'rejected', 'under_review', 'needs_revision']

# Admin Configuration
SUPER_ADMIN_EMAIL = "admin@gmail.com"
SUPER_ADMIN_PASSWORD = "admin123"

# JWT Configuration
ACCESS_TOKEN_EXPIRE_MINUTES = 1440  # 24 hours
ALGORITHM = "HS256"
