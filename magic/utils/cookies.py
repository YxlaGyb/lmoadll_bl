from typing import Optional, Any
from magic.utils.jwt import verifyJwtPayload


def setCookieToken(response: Any, token: str) -> None:
    response.set_cookie(
        'forestwhisper',
        token,
        httponly=True,
        max_age=7 * 24 * 60 * 60,
        samesite='Lax'
    )

def getCookieToken(ctx: Any) -> Optional[Any]:
    refresh_token = ctx.cookies.get('forestwhisper')
    if not refresh_token:
        return None
    try:
        user = verifyJwtPayload(refresh_token)
        return user
    except Exception as e:
        print('Get user info from cookies error', e)
