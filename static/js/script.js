function fetchPages() {
    fetch("/api/cms/list_pages")
        .then(response => {
            if (!response.ok) {
                if (response.status === 403) {
                    document.getElementById("page-list").innerHTML = "<li>Unauthorized, Please log in.</li>"
                }
                throw new Error("Request failed");
            }
            return response.json()
        })
        .then(data => {
            const pageList = document.getElementById("page-list")
            pageList.innerHTML = "";

            if (data.pages.length > 0) {
                data.pages.forEach(page => {
                    let listItem = document.createElement("li");
                    let link = document.createElement("a");
                    link.href = `/cms/edit/${page}`;
                    link.textContent = page.replace("", "");
                    listItem.appendChild(link);
                    pageList.appendChild(listItem);
                });
            } else {
                pageList.innerHTML = "<li>No pages found</li>"
            }
        })
        .catch(error => console.error("Error fetching pages:", error));
}

document.addEventListener("DOMContentLoaded", fetchPages);