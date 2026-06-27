# 虚拟人面部素材库规范

目标：把实时语音虚拟人从“临时切换整张中文表情图”推进到“统一规格的面部素材库 + 运行时状态驱动”。

## 素材目录

第一版目标目录：

```text
outputs/avatar_faces/
```

当前 `outputs/faces/` 继续作为兼容 fallback。新素材补齐前，前端仍能用现有中文脸部素材运行。

## 命名规则

文件名使用：

```text
{emotion}_{mouthShape}.png
```

`emotion` 第一版只做 5 类：

- `happy`
- `thinking`
- `surprised`
- `sad`
- `angry`

`mouthShape` 第一版只做 3 类：

- `closed`
- `open_small`
- `open_wide`

## 最小素材清单

第一版共 15 张：

```text
happy_closed.png
happy_open_small.png
happy_open_wide.png
thinking_closed.png
thinking_open_small.png
thinking_open_wide.png
surprised_closed.png
surprised_open_small.png
surprised_open_wide.png
sad_closed.png
sad_open_small.png
sad_open_wide.png
angry_closed.png
angry_open_small.png
angry_open_wide.png
```

## 图片规格

- 尺寸：沿用当前 `outputs/faces/*.png` 的尺寸和脸部框比例。
- 背景：透明背景。
- 内容：只包含小孩脸部和头盔脸屏区域，不包含舞台背景。
- 锚点：所有素材的脸中心、眼睛高度、嘴中心必须保持一致。
- 边缘：保留柔和 alpha 边缘，避免切换时出现硬边。

## 运行时状态

运行时只认两个维度：

```text
emotion + mouthShape
```

语境决定 `emotion`：

- 正常、积极：`happy`
- 用户讲话、处理中：`thinking`
- 惊讶、疑问：`surprised`
- 难过、委屈：`sad`
- 生气、不满：`angry`

声音音量决定 `mouthShape`：

- 无声音：`closed`
- 小音量：`open_small`
- 中高音量：`open_wide`

## 兼容策略

在新素材目录补齐前，前端用下面的 legacy fallback：

| 结构化状态 | fallback |
| --- | --- |
| `happy_closed` | `开心` |
| `happy_open_small` | `眨眼笑` |
| `happy_open_wide` | `大笑` |
| `thinking_closed` | `思考` |
| `thinking_open_small` | `开心` |
| `thinking_open_wide` | `惊讶` |
| `surprised_closed` | `惊讶` |
| `surprised_open_small` | `惊讶` |
| `surprised_open_wide` | `斜眼惊讶` |
| `sad_closed` | `难过` |
| `sad_open_small` | `委屈哭` |
| `sad_open_wide` | `大哭` |
| `angry_closed` | `生气` |
| `angry_open_small` | `愤怒` |
| `angry_open_wide` | `愤怒` |
