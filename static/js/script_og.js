let jsonData = null;
let classifiedMap = {};

document.addEventListener("DOMContentLoaded", function () {
  console.log("Script loaded");

  const domainSelect = document.getElementById("domainSelect");
  const productSelect = document.getElementById("productSelect");
  const fileInput = document.getElementById("fileUploader");
  const jsonPreview = document.getElementById("jsonPreview");
  const outputDiv = document.getElementById("output");
  const downloadLinkDiv = document.getElementById("downloadLink");
  const loader = document.getElementById("loader");
  const jsonEditor = CodeMirror.fromTextArea(document.getElementById("jsonEditor"), {
    mode: "javascript",
    theme: "dracula",
    lineNumbers: true,
    readOnly: true,
  });
  const codeEditor = CodeMirror.fromTextArea(document.getElementById("codeEditor"), {
    mode: "python",
    theme: "dracula",
    lineNumbers: true,
    readOnly: true,
  });

  // Populate domain and product selects dynamically
  fetch("/api/v1/edf/genai/codegenservices/get-domain-product-map")
    .then(res => res.json())
    .then(domainToProducts => {
      for (let domain in domainToProducts) {
        domainSelect.add(new Option(domain, domain));
      }

      domainSelect.addEventListener("change", () => {
        const domain = domainSelect.value;
        productSelect.innerHTML = "";
        domainToProducts[domain].forEach(p => productSelect.add(new Option(p, p)));
      });

      domainSelect.dispatchEvent(new Event("change"));
    });

  fileInput.addEventListener("change", async function (event) {
    const file = event.target.files[0];
    if (!file) return;

    const reader = new FileReader();

    if (file.name.endsWith(".json")) {
      reader.onload = function (e) {
        try {
          jsonData = JSON.parse(e.target.result);
          const prettyJson = JSON.stringify(jsonData, null, 2);
          jsonEditor.setValue(prettyJson);
        } catch (err) {
          jsonPreview.innerHTML = `<p style="color:red;">Invalid JSON file.</p>`;
        }
      };
      reader.readAsText(file);
      
    } else if (file.name.endsWith(".xlsx")) {
      const reader = new FileReader();
      reader.onload = async function (e) {
        const base64Data = e.target.result.split(',')[1]; 
        const domain = document.getElementById("domainSelect").value;
        const product = document.getElementById("productSelect").value;


        const payload = {
          user_id: 'brandon.wallace3@pepsico.com',
          domain,
          product,
          file_name: file.name,
          file_content: base64Data
        }
        console.log("Payload:", payload);
        console.log("JSON Stringified:", JSON.stringify(payload));
        try {
          const res = await fetch("/api/v1/edf/genai/codegenservices/transform-excel", {
            method: "POST",
            headers: {
              "Content-Type": "application/json"
            },
            body: JSON.stringify(payload)
          });

          const result = await res.json();
          
          let parsedContent = result.content;
          if (typeof result.content == "string") {
            parsedContent = JSON.parse(result.content);
          }
          jsonData = parsedContent;
          
          jsonEditor.setValue(JSON.stringify(parsedContent, null, 2));
          
          // jsonData = result;
          // jsonEditor.setValue(JSON.stringify(jsonData, null, 2));
          // if (result.content) {
          //   jsonData = result.content;
          //   jsonEditor.setValue(JSON.stringify(jsonData, null, 2));
          // } else if (result.error) {
          //   jsonPreview.innerHTML = '<p style="color:red;>${result.error}</p>';
          // } else {
          //   jsonPreview.innerHTML = '<p style="color:red;>Unexpected response format.</p>';
          // }
      } catch (err) {
        console.error(err);
        jsonPreview.innerHTML = `<p style="color:red;">Failed to transform Excel to JSON.</p>`;
      }
    };

    reader.readAsDataURL(file);
  }
  else {
      jsonPreview.innerHTML = `<p style="color:red;">Unsupported file type. Please upload .json or .xlsx</p>`;
    }
  });

  window.generate = async function () {
    downloadLinkDiv.innerHTML = "";
    loader.style.display = "block"; // Show spinner

    const domain = document.getElementById("domainSelect").value;
    const product = document.getElementById("productSelect").value;

    if (!jsonData) {
      loader.style.display = "none";
      alert("Please upload a valid JSON or Excel file first.");
      return;
    }

    try {
      const response = await fetch("/api/v1/edf/genai/codegenservices/generate-silver-notebook", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ user_id: 'brandon.wallace3@pepsico.com', domain: domain, product: product, prompt: jsonData })
      });

      const result = await response.json();

      if (response.status === 200 && result.data) {
        const localPath = result.data;
        const downloadUrl = `/api/v1/edf/genai/codegenservices/download-notebook?file_path=${encodeURIComponent(localPath)}`;

        console.log("🧾 Downloading from:", downloadUrl);

        const fileRes = await fetch(downloadUrl);
        const codeText = await fileRes.text();

        codeEditor.setValue(codeText);

        downloadLinkDiv.innerHTML = `
          <a href="${downloadUrl}" download>📥 Download Notebook</a>
        `;
      } else {
        outputDiv.innerHTML = `<p style="color:red;">${result.error || "Error generating notebook."}</p>`;
      }
    } catch (err) {
      console.error(err);
      outputDiv.innerHTML = `<p style="color:red;">Something went wrong while generating the notebook.</p>`;
    } finally {
      loader.style.display = "none"; // Hide spinner
    }
  };
});