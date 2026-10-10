# 布萨日 iCal 订阅 · Uposatha Calendar

根据「美德雅 / Metteyya」Android App（`cn.com.metteyya.news`）内置的缅甸历法
算法生成 Uposatha（伍波思特/布萨）日的 iCalendar 订阅源。App 中的布萨日完全由
设备本地算法计算（`MyanmarDateKernelA` + `CalendarUtil`），本仓库将该算法忠实
移植为 Python，日期与 App 一致。

## 订阅源

| 文件 | 内容 |
| --- | --- |
| `uposatha.ics` | 全部布萨日（月圆日、月黑日、上弦月、下弦月，每月 4 个）+ 五大节日 |
| `uposatha-festivals.ics` | 仅敬僧节、敬佛节、敬法节、入雨安居、出雨安居 |

事件为全天事件，中文 + 英文标题（Magha Puja / Vesak / Asalha Puja / Vassa /
Pavarana），UID 稳定，订阅后重新生成只会更新、不会重复。

## 本地生成

生成器只依赖 Python 3.10+ 标准库：

```bash
python generate_ics.py                 # 生成 前2年~后10年 到 site/
python generate_ics.py --start 2000 --end 2100 --out site
```

校验（需要 `pip install ephem`）：

```bash
python validate.py
```

校验包含三重独立验证：

1. 与同算法的 TypeScript 实现（`ref/ref_port.py`）逐日比对，2000–2050 共
   18,628 天零差异；
2. PyEphem 天文朔望时刻交叉验证（缅甸算术历与天文日可有 1–2 天偏差，弦日按
   "第八天"规则最多 3 天，属算法本身特性）；
3. 已知节日硬日期（2020/2023/2024/2025）。

## 部署到 GitHub Pages（推荐，零成本）

1. Fork / 推送本仓库到 GitHub。
2. 仓库 **Settings → Pages → Source** 选择 **GitHub Actions**。
3. 推送一次（或手动运行 Actions 中的 **Build & deploy Uposatha calendar**）。
   工作流会先跑校验、再生成 `.ics` 并部署。
4. 订阅地址（Actions 页面会显示最终域名）：
   - `https://<用户名>.github.io/<仓库名>/uposatha.ics`
   - `https://<用户名>.github.io/<仓库名>/uposatha-festivals.ics`

之后工作流每月自动重新生成一次（滚动覆盖未来 10 年），也可手动触发。
日历 App 中可用 `webcal://` 前缀，或直接粘贴 `https://` 地址。

> 如果使用自定义域名，修改 `generate_ics.py` 中的 `DEFAULT_DOMAIN`（或部署时
> 传 `--domain`），UID 会使用你的域名。**注意：订阅发布后不要更换域名**，
> 否则订阅者会看到一套全新事件。

## 部署到 Cloudflare Pages

连接 Git 仓库后，构建配置：

| 项 | 值 |
| --- | --- |
| Framework preset | None |
| Build command | `python3 generate_ics.py --out site --domain <项目名>.pages.dev && cp assets/* site/ && touch site/.nojekyll` |
| Build output directory | `site` |

Cloudflare Pages 的构建镜像自带 Python 3，无需额外依赖。部署后订阅地址：

- `https://<项目名>.pages.dev/uposatha.ics`
- `https://<项目名>.pages.dev/uposatha-festivals.ics`

## 文件说明

- `mmcalendar_kernel.py` — App 算法的忠实 Python 移植（含全部纪元常量、
  月相判定、节日规则）
- `generate_ics.py` — RFC 5545 iCal 生成器（CRLF、75 字节折行、VALUE=DATE
  全天事件、稳定 UID）
- `validate.py` — 三重校验脚本
- `ref/ref_port.py`、`ref/*.ts` — 同算法的独立参考实现（TS / 第二移植）
- `assets/index.html` — 订阅主页（自动列出近期布萨日）
- `.github/workflows/calendar.yml` — GitHub Actions 构建 + Pages 部署

## 关于 App 算法的已知怪异行为

移植严格忠实于 App 字节码，包括其硬编码闰年（2020/2023/2031/2039）带来的
特殊行为，例如：2023 年敬法节落在 8 月 1 日（闰八月规则）、2020/2031 年
无「出雨安居」标签（十月满月不在 31 日）、2039 年出雨安居为 11 月 1 日等。
这些是 App 本身的行为，本日历保持一致。

日期已与 App 实际显示核对（如 2026-10-11 月黑日、2026-10-19 上弦月、
2026-10-26 月圆日/出雨安居）。
