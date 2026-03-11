import streamlit as st
import requests
from bs4 import BeautifulSoup
from PIL import Image
import io

# 设置页面配置
st.set_page_config(page_title="网页乐谱抓取神器", page_icon="🎵", layout="centered")

st.title("🎵 网页乐谱自动提取转 PDF")
st.markdown("输入包含乐谱图片的网页地址（如微信公众号文章），自动抓取大图并生成 PDF。")

# 1. 用户输入网址
url = st.text_input("🔗 请输入文章或网页的 URL:", placeholder="https://mp.weixin.qq.com/s/...")

# 添加一个过滤选项，防止把网页上的小图标也抓进 PDF 里
min_width = st.slider("过滤掉宽度小于多少像素的图片？(防止抓取到头像、小图标)", 100, 800, 400)

if st.button("🚀 开始抓取并生成 PDF"):
    if not url:
        st.warning("⚠️ 请先输入网址！")
    else:
        try:
            with st.spinner("正在访问网页，解析内容..."):
                # 伪装成浏览器访问，防止被反爬虫拦截
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
                }
                response = requests.get(url, headers=headers, timeout=10)
                response.raise_for_status() # 检查请求是否成功
                
                # 解析网页 HTML
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # 提取所有图片标签
                img_tags = soup.find_all('img')
                img_urls = []
                
                # 兼容微信公众号(data-src)和普通网页(src)
                for img in img_tags:
                    src = img.get('data-src') or img.get('src')
                    if src and src.startswith('http'):
                        img_urls.append(src)
                
            if not img_urls:
                st.error("❌ 在该网页中没有找到任何图片。")
            else:
                st.info(f"🔍 网页解析完成，共发现 {len(img_urls)} 张潜在图片，正在过滤和下载...")
                
                valid_images = []
                # 创建进度条
                progress_bar = st.progress(0)
                
                for i, img_url in enumerate(img_urls):
                    try:
                        # 下载图片数据
                        img_response = requests.get(img_url, headers=headers, timeout=5)
                        img_data = io.BytesIO(img_response.content)
                        img = Image.open(img_data)
                        
                        # 过滤掉尺寸太小（比如头像、二维码、装饰图标）的图片
                        if img.width >= min_width:
                            # 转换为 RGB 模式（PDF 要求）
                            if img.mode != 'RGB':
                                img = img.convert('RGB')
                            valid_images.append(img)
                    except Exception as e:
                        print(f"无法处理图片 {img_url}: {e}")
                    
                    # 更新进度条
                    progress_bar.progress((i + 1) / len(img_urls))
                
                if valid_images:
                    st.success(f"✅ 成功提取了 {len(valid_images)} 张符合条件的乐谱大图！")
                    
                    # 将图片合并为 PDF 存入内存
                    pdf_buffer = io.BytesIO()
                    with st.spinner("正在合成高清 PDF..."):
                        valid_images[0].save(
                            pdf_buffer, 
                            format="PDF", 
                            save_all=True, 
                            append_images=valid_images[1:]
                        )
                    
                    # 提供下载按钮
                    st.download_button(
                        label="📥 点击下载乐谱 PDF",
                        data=pdf_buffer.getvalue(),
                        file_name="Web_Score_Extracted.pdf",
                        mime="application/pdf"
                    )
                    
                    # （可选）在网页上预览抓取到的图片
                    with st.expander("👀 预览抓取到的图片"):
                        for idx, v_img in enumerate(valid_images):
                            st.image(v_img, caption=f"第 {idx+1} 页", use_container_width=True)
                            
                else:
                    st.warning("⚠️ 抓取到了图片，但它们的尺寸都太小了，被自动过滤掉了。你可以尝试调低上面的过滤滑块。")
                    
        except Exception as e:
            st.error(f"❌ 抓取失败，请检查网址是否正确或网站是否开启了防爬虫保护。错误信息：{e}")
