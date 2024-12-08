import logging
from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import UntypedToken
from django.contrib.auth.models import AnonymousUser
import jwt
from django.contrib.auth import get_user_model

logger = logging.getLogger(__name__)
User = get_user_model()


class JWTAuthMiddleware(BaseMiddleware):
    async def __call__(self, scope, receive, send):
        logger.info("JWT Auth Middleware invoked")

        # Parse query string to get token
        query_string = parse_qs(scope["query_string"].decode())
        token = query_string.get("token", [None])[0]  # Get first token or None

        if token:
            try:
                # Validate and decode token
                UntypedToken(token)
                decoded_data = jwt.decode(token, options={"verify_signature": False})
                user_id = decoded_data.get("user_id")
                if user_id:
                    user = await self.get_user(user_id)
                    scope["user"] = user
                    logger.info(f"Authenticated user: {user}")
                else:
                    scope["user"] = AnonymousUser()
                    logger.warning("Token does not contain user_id")
            except (InvalidToken, TokenError, jwt.DecodeError) as e:
                logger.error(f"JWT Authentication failed: {e}")
                scope["user"] = AnonymousUser()
        else:
            scope["user"] = AnonymousUser()
            logger.warning("No token provided")

        return await super().__call__(scope, receive, send)

    @staticmethod
    async def get_user(user_id):
        try:
            return await database_sync_to_async(User.objects.get)(id=user_id)
        except User.DoesNotExist:
            logger.error(f"User with id {user_id} does not exist")
            return AnonymousUser()
