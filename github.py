from io import BytesIO
from pathlib import Path
from typing import Dict

import aiohttp
from PIL import Image, ImageDraw, ImageFont

error_message = {
    "404": '404 Not Found!'
}


class Github(object):

    def __init__(self):
        self.headers = {}

    async def get_repo_info(self, owner: str, repo: str, **kwargs) -> Dict:
        """
        API Docs: https://docs.github.com/cn/rest/reference/repos#get-a-repository
        :param owner: REPO的拥有者
        :param repo: REPO名称
        :return: REPO_INFO_DICT

        REPO_INFO_DICT {
        "success”: boolean, 结果状态。
        "data": {
            "name": str, repo名称
            "description": str, repo描述
            "owner": str, repo拥有者
            "avatar": str, repo_owner头像url
            "stars": int, star数量
            "watchers": int, watcher数量
            "forks": int, fork数量
            "license": str, license名称
            "status": str, 错误状态
            "message": str, 错误信息
            }
        }
        """
        url = f"https://api.github.com/repos/{owner}/{repo}"
        try:
            async with aiohttp.ClientSession(headers=self.headers, **kwargs) as session:
                async with session.get(url) as r:
                    if r.status != 200:
                        return {'success': False, 'data': {"status": str(r.status),
                                                           "message": error_message.get(str(r.status),
                                                                                        'Unknown Error!\n')}}
                    resp = await r.json()
                    repo_info = {
                        "name": resp.get("name"),
                        "description": resp.get("description"),
                        "owner": resp.get("owner", {}).get("login"),
                        "avatar": resp.get("owner", {}).get("avatar_url"),
                        "stars": resp.get("stargazers_count"),
                        "watchers": resp.get("subscribers_count"),
                        "forks": resp.get("forks"),
                        "license": resp.get("license", {}).get("spdx_id")
                    }
                    return {'success': True, 'data': repo_info}
        except Exception as e:
            return {'success': False, 'data': {"status": e,
                                               "message": e}}

    async def gen_repo_img(self, repo_info: Dict) -> Image.Image:
        """
        生成REPO预览图，长宽为800*400
        :param repo_info:
        :return: Image.Image
        """

        cut_length = 400  # Changeable

        path = Path(__file__).parent / "data"
        # im = Image.new("RGBA", (800, 400), (255, 255, 255, 255))
        im = Image.open(path / "template.png")
        draw = ImageDraw.Draw(im)
        font_path = path / "fonts"
        name_font = ImageFont.truetype(str(font_path / "msyh.ttc"), 25)
        repo_font = ImageFont.truetype(str(font_path / "msyhbd.ttc"), 30)
        desc_font = ImageFont.truetype(str(font_path / "msyh.ttc"), 15)
        count_font = ImageFont.truetype(str(font_path / "msyhbd.ttc"), 20)
        draw.text((50, 50), repo_info['owner'] + "/", fill=(50, 50, 50, 255), font=name_font)
        draw.text((50, 80), repo_info['name'], fill=(0, 0, 0, 255), font=repo_font)

        # Gen Multi Lines In Case
        size = desc_font.getsize(repo_info['description'])
        if size[0] > cut_length:
            cutter = size[0] // cut_length
            for i in range(cutter):

                length = len(repo_info['description']) // cutter
                line_text = repo_info['description'][i * length:(i + 1) * length].strip()
                draw.text((50, 120 + 25 * i), line_text, fill=(100, 100, 100, 255), font=desc_font)
                if i == cutter - 1:
                    line_text = repo_info['description'][(i + 1) * length:].strip()
                    draw.text((50, 120 + 25 * (i + 1)), line_text, fill=(100, 100, 100, 255), font=desc_font)
        else:
            draw.text((50, 120), repo_info['description'], fill=(100, 100, 100, 255), font=desc_font)

        draw.text((335, 305), str(repo_info['stars']), fill=(100, 100, 100, 255), font=count_font, align='center')
        draw.text((435, 305), str(repo_info['forks']), fill=(100, 100, 100, 255), font=count_font, align='center')

        avatar = await self.get_url_pic(repo_info['avatar'])
        avatar = avatar.resize((125, 125), Image.ANTIALIAS)
        avatar = self.img_circle(avatar, 125)
        _, _, _, a = avatar.split()
        im.paste(avatar, (600, 60), mask=a)
        return im

    async def get_url_pic(self, url: str, **kwargs) -> Image.Image:
        """
        从一个图片URL返回一个Image.Image
        :param url: str, URL
        :return: Image.Image: 图片对象
        """
        async with aiohttp.ClientSession(headers=self.headers, **kwargs) as session:
            async with session.get(url) as r:
                if r.status == 200:
                    buf = BytesIO()
                    buf.write(await r.read())
                    return Image.open(buf)

    def img_circle(self, img: Image.Image, img_width: int) -> Image.Image:
        """
        切割成圆形图片
        :param img: Image.Image, 图片对象
        :param img_width: int, 图片宽度
        :return:
        """
        x = img_width
        r = x // 2

        img_return = Image.new('RGBA', (x, x), (255, 255, 255, 0))
        img_white = Image.new('RGBA', (x, x), (255, 255, 255, 0))

        p_src = img.load()
        p_return = img_return.load()
        p_white = img_white.load()

        for i in range(x):
            lx = abs(i - r)
            for j in range(x):
                ly = abs(j - r)
                l = (pow(lx, 2) + pow(ly, 2)) ** 0.5
                if l < r:
                    p_return[i, j] = p_src[i, j]
                if l > r:
                    p_return[i, j] = p_white[i, j]
        return img_return
