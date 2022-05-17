import base64

from io import BytesIO
from nonebot import on_regex
from nonebot.typing import T_State
from nonebot.adapters.cqhttp import Bot, Event, MessageSegment
from nonebot.log import logger

from .github import Github

github_preview = on_regex(r"github.com\/(.+)?\/([^\/\s]+)", priority=10, block=True)


@github_preview.handle()
async def _(bot: Bot, event: Event, state: T_State):
    owner, repo = state['_matched_groups']
    git = Github()
    r = await git.get_repo_info(owner, repo)
    if r.get('success'):
        img = await git.gen_repo_img(r.get('data'))
        buf = BytesIO()
        img.save(buf, format='PNG')
        base64_str = base64.b64encode(buf.getvalue()).decode()
        await github_preview.finish(MessageSegment.image(f'base64://{base64_str}'))
    else:
        logger.error('API WRONG')



