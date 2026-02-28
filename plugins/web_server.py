from aiohttp import web

async def root_handler(request):
    # Health check के लिए Koyeb HTTP 200 return करता है
    return web.Response(text="Bot is running!")

async def web_server():
    app = web.Application()
    app.router.add_get("/", root_handler)  # Health check के लिए root path जरूरी
    return app
