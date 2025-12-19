# services/fyers_auth.py

"""
Fyers API Authentication Service
Handles authentication and token management
"""

import logging
from fyers_apiv3 import fyersModel
from config.settings import FyersAPIConfig

logger = logging.getLogger(__name__)


class FyersAuth:
    """Fyers API Authentication Manager"""

    def __init__(self):
        self.app_id = FyersAPIConfig.APP_ID
        self.secret_key = FyersAPIConfig.SECRET_KEY
        self.redirect_url = FyersAPIConfig.REDIRECT_URL
        self.access_token = FyersAPIConfig.ACCESS_TOKEN

        self.fyers = None
        self.is_authenticated = False

        logger.info("FyersAuth initialized")

    async def initialize(self):
        """Initialize Fyers API client"""
        try:
            if not self.access_token:
                logger.error("Access token not configured")
                raise ValueError("FYERS_ACCESS_TOKEN not set in environment")

            # Create Fyers client with access token
            self.fyers = fyersModel.FyersModel(
                client_id=self.app_id,
                token=self.access_token,
                log_path=""
            )

            # Verify token by getting profile
            profile = self.get_profile()
            if profile:
                self.is_authenticated = True
                logger.info(f" Authenticated as: {profile.get('name', 'Unknown')}")
                logger.info(f"  User ID: {profile.get('fy_id', 'Unknown')}")
                return True
            else:
                logger.error("Failed to authenticate with Fyers")
                return False

        except Exception as e:
            logger.error(f"Error initializing Fyers authentication: {e}")
            return False

    def get_profile(self):
        """Get user profile"""
        try:
            if not self.fyers:
                return None

            response = self.fyers.get_profile()

            if response.get('s') == 'ok':
                return response.get('data', {})
            else:
                logger.error(f"Failed to get profile: {response}")
                return None

        except Exception as e:
            logger.error(f"Error getting profile: {e}")
            return None

    def get_funds(self):
        """Get account funds"""
        try:
            if not self.fyers:
                return None

            response = self.fyers.funds()

            if response.get('s') == 'ok':
                return response.get('fund_limit', [])
            else:
                logger.error(f"Failed to get funds: {response}")
                return None

        except Exception as e:
            logger.error(f"Error getting funds: {e}")
            return None

    def get_client(self):
        """Get Fyers API client"""
        if not self.is_authenticated:
            logger.warning("Not authenticated - call initialize() first")
            return None
        return self.fyers

    def generate_auth_url(self):
        """
        Generate authentication URL for manual token generation
        This is a helper method for initial setup
        """
        try:
            from fyers_apiv3 import fyersModel

            session = fyersModel.SessionModel(
                client_id=self.app_id,
                secret_key=self.secret_key,
                redirect_uri=self.redirect_url,
                response_type='code',
                grant_type='authorization_code'
            )

            auth_url = session.generate_authcode()

            print("\n" + "=" * 80)
            print("FYERS AUTHENTICATION URL")
            print("=" * 80)
            print("\nVisit this URL in your browser to authorize:")
            print(f"\n{auth_url}\n")
            print("After authorization, copy the 'auth_code' from the redirect URL")
            print("Then use it to generate access token")
            print("=" * 80 + "\n")

            return auth_url

        except Exception as e:
            logger.error(f"Error generating auth URL: {e}")
            return None

    def generate_access_token(self, auth_code: str):
        """
        Generate access token from auth code
        This is a helper method for initial setup
        """
        try:
            from fyers_apiv3 import fyersModel

            session = fyersModel.SessionModel(
                client_id=self.app_id,
                secret_key=self.secret_key,
                redirect_uri=self.redirect_url,
                response_type='code',
                grant_type='authorization_code'
            )

            session.set_token(auth_code)
            response = session.generate_token()

            if response.get('s') == 'ok':
                access_token = response.get('access_token')
                print("\n" + "=" * 80)
                print("ACCESS TOKEN GENERATED")
                print("=" * 80)
                print(f"\nYour access token:\n\n{access_token}\n")
                print("Add this to your .env file as FYERS_ACCESS_TOKEN")
                print("=" * 80 + "\n")
                return access_token
            else:
                logger.error(f"Failed to generate token: {response}")
                return None

        except Exception as e:
            logger.error(f"Error generating access token: {e}")
            return None


if __name__ == "__main__":
    import asyncio


    async def test_auth():
        print("Fyers Authentication Test")
        print("=" * 60)

        auth = FyersAuth()

        # Test authentication
        success = await auth.initialize()

        if success:
            print("\n Authentication successful")

            # Get profile
            profile = auth.get_profile()
            if profile:
                print(f"\nProfile:")
                print(f"  Name: {profile.get('name')}")
                print(f"  Email: {profile.get('email_id')}")
                print(f"  PAN: {profile.get('PAN')}")

            # Get funds
            funds = auth.get_funds()
            if funds:
                print(f"\nFunds:")
                for fund in funds:
                    print(f"  {fund.get('title')}: ₹{fund.get('equityAmount', 0):,.2f}")
        else:
            print("\n✗ Authentication failed")
            print("\nTo set up authentication:")
            print("1. Run: python services/fyers_auth.py --generate-url")
            print("2. Visit the URL and authorize")
            print("3. Run: python services/fyers_auth.py --generate-token AUTH_CODE")


    # Check command line args
    import sys

    if len(sys.argv) > 1:
        auth = FyersAuth()
        if sys.argv[1] == '--generate-url':
            auth.generate_auth_url()
        elif sys.argv[1] == '--generate-token' and len(sys.argv) > 2:
            auth.generate_access_token(sys.argv[2])
    else:
        asyncio.run(test_auth())