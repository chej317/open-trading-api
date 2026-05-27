import os
required_vars = ["GH_ACCOUNT", "GH_APPKEY", "GH_APPSECRET"]
missing = [v for v in required_vars if not os.environ.get(v)]
if missing:
    print(f"Missing environment variables: {', '.join(missing)}")
else:
    print("All required environment variables are present.")
