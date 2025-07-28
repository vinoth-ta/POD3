let jsonData = null;
let classifiedMap = {};

document.addEventListener("DOMContentLoaded", function () {
  console.log("Script loaded");

  const layerClassSelect = document.getElementById("layerClassSelect");
  const domainSelect = document.getElementById("domainSelect");
  const productSelect = document.getElementById("productSelect");
  const fileInput = document.getElementById("fileUploader");
  const sheetSelect = document.getElementById("sheetSelect");
  const submitSheetBtn = document.getElementById("submitSheetBtn");
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
  // fetch("/api/v1/edf/genai/codegenservices/get-domain-product-map")
  //   .then(res => res.json())
  //   .then(domainToProducts => {
  //     for (let domain in domainToProducts) {
  //       domainSelect.add(new Option(domain, domain));
  //     }

  //     domainSelect.addEventListener("change", () => {
  //       const domain = domainSelect.value;
  //       productSelect.innerHTML = "";
  //       domainToProducts[domain].forEach(p => productSelect.add(new Option(p, p)));
  //     });

  //     domainSelect.dispatchEvent(new Event("change"));
  //   });

  fetch("/api/v1/edf/genai/codegenservices/get-classified-domain-product-map")
  .then(res => res.json())
  .then(data => {
    classifiedMap = data;

    const classifications = Object.keys(data);
    layerClassSelect.innerHTML = "";

    classifications.forEach(classification => {
      layerClassSelect.add(new Option(capitalize(classification), classification));
    });

    layerClassSelect.addEventListener("change", () => {
      const selectedClass = layerClassSelect.value;
      const domainMap = classifiedMap[selectedClass] || {};
      const domainList = Object.keys(domainMap);

      domainSelect.innerHTML = "";
      productSelect.innerHTML = "";

      if (domainList.length === 0) {
        domainSelect.add(new Option("No domains available", ""));
        productSelect.add(new Option("No products available", ""));
        return;
      }

      domainList.forEach(domain => {
        domainSelect.add(new Option(domain, domain));
      });

      domainSelect.dispatchEvent(new Event("change"));
    });

    domainSelect.addEventListener("change", () => {
      const selectedClass = layerClassSelect.value;
      const selectedDomain = domainSelect.value;

      const productList = classifiedMap[selectedClass]?.[selectedDomain] || [];
      productSelect.innerHTML = "";

      if (productList.length === 0) {
        productSelect.add(new Option("No products available", ""));
        return;
      }

      productList.forEach(product => {
        productSelect.add(new Option(product, product));
      });
    });

    layerClassSelect.dispatchEvent(new Event("change"));
  });

    //   layerClassSelect.addEventListener("change", () => {
    //     const selectedClass = layerClassSelect.value;
    //     const domains = Object.keys(classifiedMap[selectedClass] || {});
    //     domainSelect.innerHTML = "";
    //     productSelect.innerHTML = "";

    //     domains.forEach(domain => {
    //       domainSelect.add(new Option(domain, domain));
    //     });

    //     domainSelect.dispatchEvent(new Event("change"));
    //   });

    //   domainSelect.addEventListener("change", () => {
    //     const selectedClass = layerClassSelect.value;
    //     const selectedDomain = domainSelect.value;
    //     const products = classifiedMap[selectedClass]?.[selectedDomain] || [];
    //     productSelect.innerHTML = "";

    //     products.forEach(p => {
    //       productSelect.add(new Option(p, p));
    //     });
    //   });

    //   layerClassSelect.dispatchEvent(new Event("change"));
    // });

  function capitalize(str) {
      return str.charAt(0).toUpperCase() + str.slice(1);
    }
  
  function buildRequestBody({ jsonList, user_id, layer_classification, domain, product }) {
    const data = {}

    jsonList.forEach((entry, index)=> {
      const targetTable = entry.target_table;
      if (!targetTable)  return;

      const { metadata, target_table, ...json_sttm } = entry;

      const merge_key = index === 1 ? 'XTNDFSystemID, XTNDFReportingUnitID' : 'ClientID, DistributionChannelCode'
      const partition_cols = index === 1 ? 'XTNDFSystemID,' : 'SystemID'

      data[targetTable] = {
        metadata: {
          target_table_name: targetTable,
          merge_key: merge_key,
          partition_columns: partition_cols,
          merge_type: 'upsert',
          source_deduplication: 'Y',
          stale_data_handling: 'Y',
          source_partitionBy_columns: 'KAPPL, KUNNR',
          source_orderBy_columns: 'MANDT'
        },
        json_sttm
      };
    });

    return {
      meta: {
        user_id,
        layer_classification,
        domain,
        product
      },
      data
    };
  }


  fileInput.addEventListener("change", async function (event) {
  const file = event.target.files[0];
  if (!file) return;

  const domain = domainSelect.value;
  const product = productSelect.value;

  if (file.name.endsWith(".json")) {
    const reader = new FileReader();
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
  }

  else if (file.name.endsWith(".xlsx")) {
    const reader = new FileReader();
    reader.onload = function (e) {
      const data = new Uint8Array(e.target.result);
      const workbook = XLSX.read(data, { type: "array" });
      const sheetNames = workbook.SheetNames;

      // Populate dropdown
      sheetSelect.innerHTML = "";
      sheetNames.forEach(name => {
        sheetSelect.add(new Option(name, name));
      });
      
      sheetSelect.style.display = "inline";
      submitSheetBtn.style.display = "inline";
      submitSheetBtn.disabled = true;

      window.selectedExcelFile = file;
    };
    reader.readAsArrayBuffer(file);
  } else {
    jsonPreview.innerHTML = `<p style="color:red;">Unsupported file type. Please upload .json or .xlsx</p>`;
  }
  });

  sheetSelect.addEventListener("change", () => {
    submitSheetBtn.disabled = sheetSelect.value === "";
  });

  submitSheetBtn.addEventListener("click", async function () {
    const file = window.selectedExcelFile;
    const selectedSheet = sheetSelect.value;
    const classification = layerClassSelect.value
    const domain = domainSelect.value;
    const product = productSelect.value;

    if (!file || !selectedSheet) {
      alert("Please upload a file and select a sheet.");
      return;
    }

    const formData = new FormData();
    formData.append('file', file);  // File object
    formData.append('user_id', 'testemail@pepsico.com');
    formData.append('layer_classification', classification)
    formData.append('domain', domain);
    formData.append('product', product);
    formData.append('sheet_name', selectedSheet);

    try {
        const res = await fetch("/api/v1/edf/genai/codegenservices/transform-excel", {
          method: "POST",
          body: formData
        });

        const result = await res.json();

        let parsedContent = result.content;
        if (typeof parsedContent === "string") {
          parsedContent = JSON.parse(parsedContent);
        }

        jsonData = parsedContent;
        jsonEditor.setValue(JSON.stringify(parsedContent, null, 2));
      } catch (err) {
        console.error(err);
        jsonPreview.innerHTML = `<p style="color:red;">Failed to transform Excel to JSON.</p>`;
      }
  });

  // Generate notebook from JSON content
  window.generate = async function () {
    downloadLinkDiv.innerHTML = "";
    loader.style.display = "block";

    const classification = layerClassSelect.value;
    const domain = domainSelect.value;
    const product = productSelect.value;

    if (!jsonData) {
      loader.style.display = "none";
      alert("Please upload a valid JSON or Excel file first.");
      return;
    }

    // const targetTable = jsonData.target_table

    // const payload = {
    //   meta: {
    //     user_id: 'testEmail@pepsico.com',
    //     layer_classification: classification,
    //     domain: domain,
    //     product: product
    //   },
    //   data: {
    //     [targetTable]: {
    //       metadata: {
    //         target_table_name: targetTable
    //       },
    //       json_sttm: jsonData
    //     }
    //   }
    // };

    const payload = buildRequestBody({
      jsonList: jsonData,
      user_id: "testEmail@pepsico.com",
      layer_classification: classification,
      domain: domain,
      product: product,
    })

    try {
      const response = await fetch("/api/v1/edf/genai/codegenservices/generate-notebook", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify(payload)
        // body: JSON.stringify({
        //   user_id: 'testEmail@pepsico.com',
        //   layer_classification: classification,
        //   domain: domain,
        //   product: product,
        //   prompt: jsonData,
        //   meta: {}
        // })
      });

      const result = await response.json();

      if (response.status === 200 && result.data) {
        const notebookCode = result.data;
        const notebookName = result.filename

        codeEditor.setValue(notebookCode)
        
        const blob = new Blob([notebookCode], { type: "application/json "});
        const url = URL.createObjectURL(blob);

        downloadLinkDiv.innerHTML = `<a href="${url}" download="${notebookName}">📥 Download Notebook</a>`;

        // const localPath = result.data;
        // const downloadUrl = `/api/v1/edf/genai/codegenservices/download-notebook?file_path=${encodeURIComponent(localPath)}`;

        // const fileRes = await fetch(downloadUrl);
        // const codeText = await fileRes.text();

        // codeEditor.setValue(codeText);
        // downloadLinkDiv.innerHTML = `<a href="${downloadUrl}" download>📥 Download Notebook</a>`;
      } else {
        outputDiv.innerHTML = `<p style="color:red;">${result.error || "Error generating notebook."}</p>`;
      }
    } catch (err) {
      console.error(err);
      outputDiv.innerHTML = `<p style="color:red;">Something went wrong while generating the notebook.</p>`;
    } finally {
      loader.style.display = "none";
    }
  };
});