import streamlit as st
import httpx
import asyncio
from urllib.parse import urlparse
from collections import defaultdict
from bs4 import BeautifulSoup
from transformers import pipeline


def get_domain(url):
    parsed_url = urlparse(url)
    return parsed_url.netloc


def categorize_by_domain(urls):
    domain_counts = defaultdict(int)
    for url in urls:
        domain = get_domain(url['href'])
        domain_counts[domain] += 1
    return domain_counts


def parse_bookmarks(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    bookmarks = []
    for link in soup.find_all('a'):
        bookmarks.append({'href': link.get('href'), 'title': link.get_text()})
    return bookmarks


async def check_url(url):
    try:
        async with httpx.AsyncClient(verify=False) as client:
            response = await client.get(url['href'], timeout=5)
            return response.status_code == 200
    except httpx.RequestError:
        return False


async def check_urls(urls):
    return await asyncio.gather(*(check_url(url) for url in urls))


def organize_bookmarks(bookmarks, categories):
    classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")

    categorized_bookmarks = {category: [] for category in categories}
    progress_bar = st.progress(0)
    total_bookmarks = len(bookmarks)

    for index, bookmark in enumerate(bookmarks[:300]):
        title = bookmark["title"]

        result = classifier(title, candidate_labels=categories)
        category = result['labels'][0]
        categorized_bookmarks[category].append(bookmark)

        progress_bar.progress((index + 1) / total_bookmarks)
    
    progress_bar.progress(100)

    return categorized_bookmarks


def find_duplicates(bookmarks):
    url_counts = {}
    for bookmark in bookmarks:
        if bookmark['href'] in url_counts:
            url_counts[bookmark['href']]['count'] += 1
        else:
            url_counts[bookmark['href']] = {'count': 1, 'bookmark': bookmark}

    duplicates = {url: item for url, item in url_counts.items() if item['count'] > 1}
    return duplicates


st.set_page_config(page_title='Bookmark Organizer', layout="wide")
st.markdown(
    """
    <style>
    .big-font {
        font-size:300% !important;
    }
    .scrolling-wrapper {
        overflow-y: auto;
        height: 300px;
        border: 1px solid #4d4d4d;
        border-radius: 7px;
        padding: 5px 15px;
    }
    .centered-message {
        text-align: center;
        font-size: 150%;
        margin-top: 70px;
    }
    </style>
    """, unsafe_allow_html=True)
col1, col2 = st.columns(2)
with col1:
    st.markdown('<p class="big-font">Bookmark Organizer</p>', unsafe_allow_html=True)
with col2:
    uploaded_file = st.file_uploader("Upload your bookmarks file", type=["html"])

if not uploaded_file:
    # st.write("No file uploaded. Please upload a bookmarks file in HTML format.")
    st.markdown('<p class="centered-message">No file uploaded. Please upload a bookmarks file in HTML format.</p>', unsafe_allow_html=True)
else:
    bookmarks = parse_bookmarks(uploaded_file.getvalue().decode())
    st.write(f"Found {len(bookmarks)} bookmarks")
    col1, col2 = st.columns(2)

    with col1:
        if st.button('Check URL Activity'):
            with st.spinner('Checking URLs...'):
                active_flags = asyncio.run(check_urls(bookmarks))
                active_urls = [url for url, active in zip(bookmarks, active_flags) if active]
                inactive_urls = [url for url, active in zip(bookmarks, active_flags) if not active]

            st.write(f"Active URLs: {len(active_urls)}")
            st.write(f"Inactive URLs: {len(inactive_urls)}")
    
    with col2:
        # Display URLs by Domain
        if st.button('Display URLs by Domain'):
            st.subheader("Domains")
            domain_counts = categorize_by_domain(bookmarks)
            total_domains = len(domain_counts)
            st.write(f"Total distinct domains: {total_domains}")
            
            with st.container():
                text = ''
                i = 1
                for domain, count in sorted(domain_counts.items(), key=lambda x: x[1], reverse=True):
                    text += f"<div>{i}) <a href='{domain}' target='_blank'>{domain}</a>: {count}</div>"
                    i += 1
                st.markdown(f'<div class="scrolling-wrapper">{text}</div>', unsafe_allow_html=True)

            # st.write(f"Total distinct domains: {total_domains}")
            # for domain, count in sorted(domain_counts.items(), key=lambda x: x[1], reverse=True):
            #     st.write(f"{domain}: {count}")
    
    st.divider()
    if st.button('Show Duplicates'):
        duplicates = find_duplicates(bookmarks)
        if duplicates:
            st.write(f"Duplicate URLs found ({len(duplicates)}):")
            for url, details in duplicates.items():
                st.markdown(f"<a href='{url}' target='_blank'>{details['bookmark']['title']}</a> - {details['count']} times", unsafe_allow_html=True)
        else:
            st.write("No duplicate URLs found.")

    st.divider()
    categories = st.text_input(
        "Enter categories separated by commas",
        value=(
            "Business"
            ", Careers"
            ", News / Information"
            ", Technology & Computing"
            ", Other"
            ", Security"
            ", Python"
            ", Scala"
            ", C++"
            ", Golang"
            ", Distributed Systems"
            ", Soft skills / Communication / Behaviour"
            ", Internationalization"
        )
    )

    # Organize button
    if st.button("Organize Bookmarks"):
        if categories:
            categorized_bookmarks = organize_bookmarks(bookmarks, categories.split(','))
            for category, bookmarks in categorized_bookmarks.items():
                with st.expander(f"Category: {category} ({len(bookmarks)} Bookmarks)"):
                    for bookmark in bookmarks:
                        title = bookmark["title"]
                        url = bookmark["href"]
                        st.markdown(f"- [{title}]({url})")  # Markdown to display link

        else:
            st.warning("Please enter some categories")
