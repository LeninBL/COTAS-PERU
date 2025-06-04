document.addEventListener("DOMContentLoaded", function () {
  // Variables globales
  let currentPage = 1;
  const rowsPerPage = 10;
  let allProducts = [];
  let filteredProducts = [];
  let sortColumn = null;
  let sortDirection = "asc";
  let ubicaciones = [
    { id: "ALMACÉN 1", nombre: "ALMACÉN 1" },
    { id: "ALMACÉN 2", nombre: "ALMACÉN 2" },
    { id: "SÓTANO", nombre: "SÓTANO" },
  ];
  let categorias = [];

  // Elementos del DOM
  const tableBody = document.querySelector("#productsTable tbody");
  const prevPageBtn = document.getElementById("prevPage");
  const nextPageBtn = document.getElementById("nextPage");
  const pageInfo = document.getElementById("pageInfo");
  const productSearch = document.getElementById("productSearch");
  const categoryFilter = document.getElementById("categoryFilter");
  const locationFilter = document.getElementById("locationFilter");
  const clearFiltersBtn = document.getElementById("clearFilters");
  const newProductBtn = document.getElementById("newProductBtn");
  const productModal = document.getElementById("productModal");
  const modalTitle = document.getElementById("modalTitle");
  const productForm = document.getElementById("productForm");
  const cancelBtn = document.getElementById("cancelBtn");
  const exportExcelBtn = document.getElementById("exportExcel");
  const closeModal = document.getElementsByClassName("close")[0];

  // Inicialización
  init();

  function init() {
    updateLocationFilters();
    loadCategoriasDinamicas();
    loadProducts();
    setupEventListeners();
  }

  function loadProducts() {
    fetch("http://127.0.0.1:8000/productos-carga")
      .then(async (response) => {
        if (!response.ok) {
          const errorText = await response.text();
          throw new Error(
            `Error ${response.status}: ${response.statusText} - ${errorText}`
          );
        }
        return response.json();
      })
      .then((data) => {
        allProducts = data;
        filteredProducts = [...allProducts];
        updateTable();
      })
      .catch((error) => {
        console.error("Error en loadProducts:", error);
        Swal.fire("Error", error.message, "error");
      });
  }

  function updateLocationFilters() {
    const locationFilter = document.getElementById("locationFilter");
    const ubicacionSelect = document.getElementById("ubicacion");

    // Limpiar opciones existentes excepto la primera
    [locationFilter, ubicacionSelect].forEach((select) => {
      while (select.options.length > 1) select.remove(1);
      ubicaciones.forEach((ubicacion) => {
        const option = new Option(ubicacion.nombre, ubicacion.nombre);
        select.add(option);
      });
    });
  }

  function updateCategoryFilters() {
    const categoryFilter = document.getElementById("categoryFilter");
    const categoriaSelect = document.getElementById("categoria");

    // Limpiar opciones existentes excepto la primera
    [categoryFilter, categoriaSelect].forEach((select) => {
      while (select.options.length > 1) select.remove(1);
      categorias.forEach((categoria) => {
        const option = new Option(categoria.nombre, categoria.nombre);
        select.add(option);
      });

      if (select.id === "categoria") {
        const newOption = new Option("+ Nueva categoría", "_nueva_categoria_");
        select.add(newOption);
      }
    });
  }

  function loadCategoriasDinamicas() {
    fetch("http://127.0.0.1:8000/categorias-dinamicas")
      .then((response) => {
        if (!response.ok) throw new Error(`Error HTTP: ${response.status}`);
        return response.json();
      })
      .then((data) => {
        categorias = [...new Set(data)]
          .filter((c) => c)
          .sort()
          .map((c) => ({ id: c, nombre: c }));
        updateCategoryFilters();
      })
      .catch((error) => {
        console.error("Error cargando categorías:", error);
        Swal.fire("Error", "No se pudieron cargar las categorías", "error");
      });
  }

  function setupEventListeners() {
    // Paginación
    prevPageBtn.addEventListener("click", () => {
      if (currentPage > 1) {
        currentPage--;
        updateTable();
      }
    });

    nextPageBtn.addEventListener("click", () => {
      const totalPages = Math.ceil(filteredProducts.length / rowsPerPage);
      if (currentPage < totalPages) {
        currentPage++;
        updateTable();
      }
    });

    // Búsqueda y filtros
    productSearch.addEventListener("input", applyFilters);
    categoryFilter.addEventListener("change", applyFilters);
    locationFilter.addEventListener("change", applyFilters);
    clearFiltersBtn.addEventListener("click", clearFilters);

    // Ordenamiento
    document.querySelectorAll("[data-sort]").forEach((header) => {
      header.addEventListener("click", () => {
        const column = header.getAttribute("data-sort");
        if (sortColumn === column) {
          sortDirection = sortDirection === "asc" ? "desc" : "asc";
        } else {
          sortColumn = column;
          sortDirection = "asc";
        }
        sortProducts();
        updateTable();
        updateSortIndicator();
      });
    });

    // Modal de producto
    newProductBtn.addEventListener("click", () => openProductModal());
    closeModal.addEventListener(
      "click",
      () => (productModal.style.display = "none")
    );
    cancelBtn.addEventListener(
      "click",
      () => (productModal.style.display = "none")
    );
    window.addEventListener("click", (event) => {
      if (event.target === productModal) {
        productModal.style.display = "none";
      }
    });

    // Formulario de producto
    productForm.addEventListener("submit", handleFormSubmit);

    // Botones de acción en la tabla
    tableBody.addEventListener("click", (e) => {
      const target = e.target.closest(".action-btn");
      if (!target) return;

      const productId = parseInt(target.getAttribute("data-id"));
      const product = allProducts.find((p) => p.id === productId);
      if (!product) return;

      if (target.classList.contains("view-btn")) {
        viewProductDetails(product);
      } else if (target.classList.contains("edit-btn")) {
        openProductModal(product);
      } else if (target.classList.contains("delete-btn")) {
        deleteProduct(productId);
      }
    });

    // Exportar a Excel
    exportExcelBtn.addEventListener("click", exportToExcel);

    // Validación de cantidades en tiempo real
    document
      .getElementById("cantidad_total")
      .addEventListener("input", validateQuantities);
    document
      .getElementById("cantidad_nuevos")
      .addEventListener("input", validateQuantities);
    document
      .getElementById("cantidad_usados")
      .addEventListener("input", validateQuantities);
    document
      .getElementById("cantidad_danados")
      .addEventListener("input", validateQuantities);

    // Manejo de nueva categoría
    document
      .getElementById("categoria")
      .addEventListener("change", function () {
        if (this.value === "_nueva_categoria_") {
          Swal.fire({
            title: "Nueva categoría",
            input: "text",
            inputPlaceholder: "Nombre de la nueva categoría",
            showCancelButton: true,
            confirmButtonText: "Guardar",
            cancelButtonText: "Cancelar",
            inputValidator: (value) => {
              if (!value) return "Debes ingresar un nombre para la categoría";
            },
          }).then((result) => {
            if (result.isConfirmed) {
              const nuevaCategoria = result.value;
              categorias.push({ id: nuevaCategoria, nombre: nuevaCategoria });
              updateCategoryFilters();
              document.getElementById("categoria").value = nuevaCategoria;
            } else {
              document.getElementById("categoria").value = "";
            }
          });
        }
      });
  }

  function updateTable() {
    const start = (currentPage - 1) * rowsPerPage;
    const end = start + rowsPerPage;
    const paginatedProducts = filteredProducts.slice(start, end);

    let html = "";
    paginatedProducts.forEach((product) => {
      html += `
            <tr data-id="${product.id}">
              <td data-label="Código"><span>${product.codigo}</span></td>
              <td data-label="Ubicación"><span>${product.ubicacion}</span></td>
              <td data-label="Categoría"><span>${
                product.categoria || ""
              }</span></td>
              <td data-label="Descripción" class="description"><span>${
                product.descripcion || ""
              }</span></td>
              <td data-label="Marca"><span>${product.marca || ""}</span></td>
              <td data-label="Modelo"><span>${product.modelo || ""}</span></td>
              <td data-label="Estado">
                <span>
                  Nuevo: ${product.cantidad_nuevos}<br>
                  Usado: ${product.cantidad_usados}<br>
                  Dañado: ${product.cantidad_danados}
                </span>
              </td>
              <td data-label="Cantidad"><span>${
                product.cantidad_total
              }</span></td>
              <td data-label="Acciones" class="actions">
                <button class="action-btn view-btn" data-id="${
                  product.id
                }"><i class="fas fa-eye"></i></button>
                <button class="action-btn edit-btn" data-id="${
                  product.id
                }"><i class="fas fa-edit"></i></button>
                <button class="action-btn delete-btn" data-id="${
                  product.id
                }"><i class="fas fa-trash"></i></button>
              </td>
            </tr>
          `;
    });
    tableBody.innerHTML = html;

    // Actualizar controles de paginación
    const totalPages = Math.ceil(filteredProducts.length / rowsPerPage);
    pageInfo.textContent = `Página ${currentPage} de ${totalPages}`;
    prevPageBtn.disabled = currentPage === 1;
    nextPageBtn.disabled = currentPage === totalPages || totalPages === 0;
  }

  function applyFilters() {
    const searchTerm = productSearch.value.toLowerCase();
    const category = categoryFilter.value;
    const location = locationFilter.value;

    filteredProducts = allProducts.filter((product) => {
      const matchesSearch = [
        product.codigo,
        product.nombre,
        product.descripcion,
        product.marca,
        product.modelo,
      ].some((field) => field && field.toLowerCase().includes(searchTerm));

      const matchesCategory = !category || product.categoria === category;
      const matchesLocation =
        !location || product.ubicacion.toLowerCase() === location.toLowerCase();

      return matchesSearch && matchesCategory && matchesLocation;
    });

    currentPage = 1;
    updateTable();
  }

  function clearFilters() {
    productSearch.value = "";
    categoryFilter.value = "";
    locationFilter.value = "";
    applyFilters();
  }

  function sortProducts() {
    if (!sortColumn) return;

    filteredProducts.sort((a, b) => {
      let valueA = a[sortColumn] || "";
      let valueB = b[sortColumn] || "";

      if (sortColumn.includes("cantidad")) {
        valueA = parseFloat(valueA);
        valueB = parseFloat(valueB);
        return sortDirection === "asc" ? valueA - valueB : valueB - valueA;
      }

      if (typeof valueA === "string") valueA = valueA.toLowerCase();
      if (typeof valueB === "string") valueB = valueB.toLowerCase();

      if (valueA < valueB) return sortDirection === "asc" ? -1 : 1;
      if (valueA > valueB) return sortDirection === "asc" ? 1 : -1;
      return 0;
    });
  }

  function updateSortIndicator() {
    document.querySelectorAll("[data-sort]").forEach((header) => {
      const icon = header.querySelector("i");
      if (header.getAttribute("data-sort") === sortColumn) {
        icon.className =
          sortDirection === "asc" ? "fas fa-sort-up" : "fas fa-sort-down";
      } else {
        icon.className = "fas fa-sort";
      }
    });
  }

  function openProductModal(product = null) {
    productForm.reset();
    document
      .querySelectorAll(".error-message")
      .forEach((el) => (el.textContent = ""));

    if (product) {
      modalTitle.textContent = "Editar Producto";
      document.getElementById("productId").value = product.id;
      document.getElementById("codigo").value = product.codigo;
      document.getElementById("nombre").value = product.nombre;
      document.getElementById("descripcion").value = product.descripcion || "";
      document.getElementById("categoria").value = product.categoria || "";
      document.getElementById("marca").value = product.marca || "";
      document.getElementById("modelo").value = product.modelo || "";
      document.getElementById("ubicacion").value = product.ubicacion;
      document.getElementById("cantidad_total").value = product.cantidad_total;
      document.getElementById("cantidad_nuevos").value =
        product.cantidad_nuevos;
      document.getElementById("cantidad_usados").value =
        product.cantidad_usados;
      document.getElementById("cantidad_danados").value =
        product.cantidad_danados;
    } else {
      modalTitle.textContent = "Nuevo Producto";
      document.getElementById("productId").value = "";
      document.getElementById("cantidad_nuevos").value = 0;
      document.getElementById("cantidad_usados").value = 0;
      document.getElementById("cantidad_danados").value = 0;
    }

    productModal.style.display = "block";
  }

  function validateQuantities() {
    const total =
      parseInt(document.getElementById("cantidad_total").value) || 0;
    const nuevos =
      parseInt(document.getElementById("cantidad_nuevos").value) || 0;
    const usados =
      parseInt(document.getElementById("cantidad_usados").value) || 0;
    const danados =
      parseInt(document.getElementById("cantidad_danados").value) || 0;
    const sum = nuevos + usados + danados;

    if (sum > total) {
      document
        .getElementById("cantidad_total")
        .setCustomValidity(
          "La suma de cantidades por estado no puede ser mayor que la cantidad total"
        );
    } else {
      document.getElementById("cantidad_total").setCustomValidity("");
    }
  }

  async function handleFormSubmit(e) {
    e.preventDefault();

    const productId = document.getElementById("productId").value;
    const isEdit = !!productId;
    const ubicacion = document.getElementById("ubicacion").value;

    // Validar campos requeridos antes de enviar
    const requiredFields = {
      codigo: "Código",
      nombre: "Nombre",
      ubicacion: "Ubicación",
      cantidad_total: "Cantidad Total",
    };

    let missingFields = [];
    for (const [field, name] of Object.entries(requiredFields)) {
      const value = document.getElementById(field).value.trim();
      if (!value) {
        missingFields.push(name);
      }
    }

    if (missingFields.length > 0) {
      Swal.fire(
        "Error",
        `Los siguientes campos son requeridos: ${missingFields.join(", ")}`,
        "error"
      );
      return;
    }

    // Validar ubicación
    if (!ubicaciones.some((u) => u.nombre === ubicacion)) {
      Swal.fire("Error", "Seleccione una ubicación válida", "error");
      return;
    }

    // Construir el objeto de datos del producto
    const productData = {
      codigo: document.getElementById("codigo").value.trim(),
      nombre: document.getElementById("nombre").value.trim(),
      descripcion: document.getElementById("descripcion").value.trim() || null,
      categoria: document.getElementById("categoria").value || null,
      marca: document.getElementById("marca").value.trim() || null,
      modelo: document.getElementById("modelo").value.trim() || null,
      ubicacion: ubicacion,
      cantidad_total: parseInt(document.getElementById("cantidad_total").value),
      cantidad_nuevos:
        parseInt(document.getElementById("cantidad_nuevos").value) || 0,
      cantidad_usados:
        parseInt(document.getElementById("cantidad_usados").value) || 0,
      cantidad_danados:
        parseInt(document.getElementById("cantidad_danados").value) || 0,
    };

    // Validación de cantidades
    if (
      productData.cantidad_total !==
      productData.cantidad_nuevos +
        productData.cantidad_usados +
        productData.cantidad_danados
    ) {
      Swal.fire(
        "Error",
        "La suma de cantidades por estado no coincide con la cantidad total",
        "error"
      );
      return;
    }

    try {
      const url = isEdit
        ? `http://127.0.0.1:8000/productos/${productId}`
        : "http://127.0.0.1:8000/productos";
      const method = isEdit ? "PUT" : "POST";

      const response = await fetch(url, {
        method: method,
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(productData),
        credentials: "include",
      });

      if (!response.ok) {
        const errorData = await response.json();
        console.error("Detalles del error:", errorData);

        let errorMessage = "Error al guardar el producto";
        if (errorData.detail) {
          if (Array.isArray(errorData.detail)) {
            errorMessage = errorData.detail
              .map((err) => {
                return err.loc ? `${err.loc[1]}: ${err.msg}` : err.msg;
              })
              .join("\n");
          } else if (typeof errorData.detail === "string") {
            errorMessage = errorData.detail;
          } else if (typeof errorData.detail === "object") {
            errorMessage = Object.values(errorData.detail).join(", ");
          }
        }

        throw new Error(errorMessage);
      }

      const result = await response.json();

      Swal.fire(
        "Éxito",
        isEdit
          ? "Producto actualizado correctamente"
          : "Producto creado correctamente",
        "success"
      ).then(() => {
        productModal.style.display = "none";
        loadProducts();

        // Actualizar lista de categorías si es nueva
        if (
          !isEdit &&
          productData.categoria &&
          !categorias.some((c) => c.nombre === productData.categoria)
        ) {
          categorias.push({
            id: productData.categoria,
            nombre: productData.categoria,
          });
          updateCategoryFilters();
        }
      });
    } catch (error) {
      console.error("Error completo:", error);
      Swal.fire({
        title: "Error",
        html: `<div style="text-align:left; white-space: pre-line;">${error.message}</div>`,
        icon: "error",
        confirmButtonText: "Entendido",
      });
    }
  }

  function viewProductDetails(product) {
    Swal.fire({
      title: `Detalles del Producto: ${product.codigo}`,
      html: `
            <div style="text-align: left;">
              <p><strong>Nombre:</strong> ${product.nombre}</p>
              <p><strong>Descripción:</strong> ${
                product.descripcion || "N/A"
              }</p>
              <p><strong>Categoría:</strong> ${product.categoria || "N/A"}</p>
              <p><strong>Marca:</strong> ${product.marca || "N/A"}</p>
              <p><strong>Modelo:</strong> ${product.modelo || "N/A"}</p>
              <p><strong>Ubicación:</strong> ${product.ubicacion}</p>
              <p><strong>Cantidad Total:</strong> ${product.cantidad_total}</p>
              <p><strong>Estado:</strong></p>
              <ul>
                <li>Nuevos: ${product.cantidad_nuevos}</li>
                <li>Usados: ${product.cantidad_usados}</li>
                <li>Dañados: ${product.cantidad_danados}</li>
              </ul>
              <p><strong>Fecha Creación:</strong> ${new Date(
                product.fecha_creacion
              ).toLocaleString()}</p>
              <p><strong>Última Actualización:</strong> ${new Date(
                product.fecha_actualizacion
              ).toLocaleString()}</p>
            </div>
          `,
      showConfirmButton: true,
      confirmButtonText: "Cerrar",
      showCancelButton: true,
      cancelButtonText: "Editar",
      focusConfirm: false,
    }).then((result) => {
      if (result.isDismissed && result.dismiss === "cancel") {
        openProductModal(product);
      }
    });
  }

  function deleteProduct(productId) {
    Swal.fire({
      title: "¿Estás seguro?",
      text: "¡No podrás revertir esto!",
      icon: "warning",
      showCancelButton: true,
      confirmButtonColor: "#3085d6",
      cancelButtonColor: "#d33",
      confirmButtonText: "Sí, eliminar",
      cancelButtonText: "Cancelar",
    }).then((result) => {
      if (result.isConfirmed) {
        fetch(`http://127.0.0.1:8000/productos/${productId}`, {
          method: "DELETE",
          credentials: "include",
        })
          .then((response) => {
            if (!response.ok) throw new Error("Error al eliminar el producto");
            return response.json();
          })
          .then(() => {
            Swal.fire("Eliminado", "El producto ha sido eliminado.", "success");
            loadProducts();
          })
          .catch((error) => {
            console.error("Error:", error);
            Swal.fire("Error", "No se pudo eliminar el producto", "error");
          });
      }
    });
  }

  function exportToExcel() {
    const data = filteredProducts.map((product) => ({
      Código: product.codigo,
      Nombre: product.nombre,
      Descripción: product.descripcion || "",
      Categoría: product.categoria || "",
      Marca: product.marca || "",
      Modelo: product.modelo || "",
      Ubicación: product.ubicacion,
      "Cantidad Total": product.cantidad_total,
      Nuevos: product.cantidad_nuevos,
      Usados: product.cantidad_usados,
      Dañados: product.cantidad_danados,
      "Fecha Creación": new Date(product.fecha_creacion).toLocaleString(),
      "Última Actualización": new Date(
        product.fecha_actualizacion
      ).toLocaleString(),
    }));

    const ws = XLSX.utils.json_to_sheet(data);
    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, ws, "Productos");
    const date = new Date().toISOString().slice(0, 10);
    XLSX.writeFile(wb, `Productos_${date}.xlsx`);
  }
});
