""" Aioauth-client example. """

import asyncio

from aiohttp import web
import html
from aioauth_client import (
    FacebookClient,
    GithubClient,
    GoogleClient,
    OAuth1Client,
    TwitterClient,
    VKClient,
    YandexClient,
)


app = web.Application()
clients = {
    'twitter': {
        'class': TwitterClient,
        'init': {
            'consumer_key': 'oUXo1M7q1rlsPXm4ER3dWnMt8',
            'consumer_secret': 'YWzEvXZJO9PI6f9w2FtwUJenMvy9SPLrHOvnNkVkc5LdYjKKup',
        },
    },
    'github': {
        'class': GithubClient,
        'init': {
            'client_id': 'b6281b6fe88fa4c313e6',
            'client_secret': '21ff23d9f1cad775daee6a38d230e1ee05b04f7c',
        },
    },
    'google': {
        'class': GoogleClient,
        'init': {
            'client_id': '150775235058-9fmas709maee5nn053knv1heov12sh4n.apps.googleusercontent.com', # noqa
            'client_secret': 'df3JwpfRf8RIBz-9avNW8Gx7',
            'params': {'scope': 'email profile'},
        },
    },
    'yandex': {
        'class': YandexClient,
        'init': {
            'client_id': 'e19388a76a824b3385f38beec67f98f1',
            'client_secret': '1d2e6fdcc23b45849def6a34b43ac2d8',
        },
    },
    'vk': {
        'class': VKClient,
        'init': {
            'client_id': '5038699',
            'client_secret': 'WgKadvY82wlnleOAyw6T',
            'params': {'scope': 'offline,email'}
        },
    },
    'facebook': {
        'class': FacebookClient,
        'init': {
            'client_id': '384739235070641',
            'client_secret': '8e3374a4e1e91a2bd5b830a46208c15a',
            'params': {'scope': 'email'}
        },
    },
}


@asyncio.coroutine
def index(request):
    return web.Response(text="""
        <ul>
            <li><a href="/oauth/facebook">Login with Facebook</a></li>
            <li><a href="/oauth/github">Login with Github</a></li>
            <li><a href="/oauth/google">Login with Google</a></li>
            <li><a href="/oauth/twitter">Login with Twitter</a></li>
            <li><a href="/oauth/vk">Login with VK</a></li>
        </ul>
    """, content_type="text/html")


# Simple Github (OAuth2) example (not connected to app)
@asyncio.coroutine
def github(request):
    github = GithubClient(
        client_id='b6281b6fe88fa4c313e6',
        client_secret='21ff23d9f1cad775daee6a38d230e1ee05b04f7c',
    )
    if 'code' not in request.GET:
        return web.HTTPFound(github.get_authorize_url(scope='user:email'))

    # Get access token
    code = request.GET['code']
    token = yield from github.get_access_token(code)
    assert token

    # Get a resource `https://api.github.com/user`
    response = yield from github.request('GET', 'user')
    body = yield from response.read()
    return web.Response(body=body, content_type='application/json')


@asyncio.coroutine
def oauth(request):
    provider = request.match_info.get('provider')
    if provider not in clients:
        raise web.HTTPNotFound(reason='Unknown provider')

    # Create OAuth1/2 client
    Client = clients[provider]['class']
    client = Client(
        redirect_uri='http://%s%s' % (request.host, request.path), **clients[provider]['init'])

    # Check if is not redirect from provider
    if client.shared_key not in request.GET:

        # For oauth1 we need more work
        if isinstance(client, OAuth1Client):
            token, secret = yield from client.get_request_token()

            # Dirty save a token_secret
            # Dont do it in production
            request.app.secret = secret
            request.app.token = token

        # Redirect client to provider
        params = clients[provider].get('params', {})
        return web.HTTPFound(client.get_authorize_url(**params))

    # For oauth1 we need more work
    if isinstance(client, OAuth1Client):
        client.oauth_token_secret = request.app.secret
        client.oauth_token = request.app.token

    yield from client.get_access_token(request.GET)
    user, info = yield from client.user_info()
    text = (
        "<a href='/'>back</a><br/><br/>"
        "<ul>"
        "<li>ID: %(id)s</li>"
        "<li>Username: %(username)s</li>"
        "<li>First, last name: %(first_name)s, %(last_name)s</li>"
        "<li>Gender: %(gender)s</li>"
        "<li>Email: %(email)s</li>"
        "<li>Link: %(link)s</li>"
        "<li>Picture: %(picture)s</li>"
        "<li>Country, city: %(country)s, %(city)s</li>"
        "</ul>"
    ) % user.__dict__
    text += "<code>%s</code>" % html.escape(repr(info))
    return web.Response(text=text, content_type='text/html')


app.router.add_route('GET', '/', index)
app.router.add_route('GET', '/oauth/{provider}', oauth)

loop = asyncio.get_event_loop()
f = loop.create_server(app.make_handler(), '127.0.0.1', 5000)
srv = loop.run_until_complete(f)
print('serving on', srv.sockets[0].getsockname())
try:
    loop.run_forever()
except KeyboardInterrupt:
    pass

# pylama:ignore=D
