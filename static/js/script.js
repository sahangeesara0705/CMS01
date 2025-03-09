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

            if (pageList) {
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
            }
        })
        .catch(error => console.error("Error fetching pages:", error));
}

document.addEventListener("DOMContentLoaded", fetchPages);

function fetchFiles() {
    fetch("/api/cms/list_files")
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
            const fileList = document.getElementById("file-list")
            fileList.innerHTML = "";

            if (data.files.length > 0) {
                data.files.forEach(file => {
                    let listItem = document.createElement("li");

                    listItem.setAttribute("data-mime-type", file.mime_type);
                    listItem.setAttribute("data-size", formatFileSize(file.size));
                    listItem.setAttribute("data-filename", file.name)

                    let link = document.createElement("a");
                    link.href = `#`;
                    link.textContent = file.name;
                    /* link.target = "_blank"; */

                    let details = document.createElement("span");
                    details.textContent = ` (${file.mime_type}, ${formatFileSize(file.size)})`;

                    listItem.appendChild(link);
                    listItem.appendChild(details);

                    listItem.addEventListener("click", function() {
                        displayFileInfo(this);
                    });

                    fileList.appendChild(listItem);
                });
            } else {
                pageList.innerHTML = "<li>No files found</li>";
            }
        })
        .catch(error => console.error("Error fetching files:", error));
}

function displayFileInfo(listItem) {
    const infoBar = document.getElementById("file-info");
    if (!infoBar) return;

    const fileName = listItem.getAttribute("data-filename");
    const mimeType = listItem.getAttribute("data-mime-type");
    const fileSize = listItem.getAttribute("data-size");

    infoBar.innerHTML = `
        <strong>Filename:</strong> ${fileName} <br>
        <strong>MIME Type:</strong> ${mimeType} <br>
        <strong>Size:</strong> ${fileSize}
    `;
}

function  formatFileSize(bytes) {
    if (bytes < 1024) return bytes + "B";
    let kb = bytes / 1024;
    if (kb < 1024) return kb.toFixed(2) + " KB";
    let mb = kb / 1024;
    return mb.toFixed(2) + " MB";
}

document.addEventListener("DOMContentLoaded", fetchFiles);