document.addEventListener("DOMContentLoaded", function () {
  // Configuración común para entradas y salidas
  const tipoMovimiento = window.location.pathname.includes("entradas")
    ? "entrada"
    : "salida";
  const formId = `${tipoMovimiento}Form`;
  const tableId = `${tipoMovimiento}sTable`;

  // Elementos del DOM
  const movimientoForm = document.getElementById(formId);
  const movimientoTable = document.getElementById(tableId);
  const registrarBtn = document.getElementById(
    `registrar${
      tipoMovimiento.charAt(0).toUpperCase() + tipoMovimiento.slice(1)
    }`
  );
  const buscarBtn = document.getElementById(
    `buscarProducto${
      tipoMovimiento.charAt(0).toUpperCase() + tipoMovimiento.slice(1)
    }`
  );

  // Inicialización
  if (movimientoForm) setupForm();
  if (movimientoTable) loadInitialMovimientos();

  function setupForm() {
    if (buscarBtn) {
      buscarBtn.addEventListener("click", buscarProducto);
    }
    if (movimientoForm) {
      movimientoForm.addEventListener("submit", handleFormSubmit);
    }

    // Configurar fecha actual si no está definida
    const fechaInput = document.getElementById(`fecha_${tipoMovimiento}`);
    if (fechaInput && !fechaInput.value) {
      const today = new Date().toISOString().split("T")[0];
      fechaInput.value = today;
    }
  }

  function loadInitialMovimientos() {
    // Los movimientos iniciales se cargan desde el servidor en la plantilla
    // Esta función es para futuras actualizaciones dinámicas
    const tbody = document.querySelector(`#${tableId} tbody`);
    if (!tbody) return;

    // Si ya hay datos cargados (desde el servidor), no hacemos nada
    if (tbody.children.length > 0) return;

    // Si no hay datos, cargamos del API
    loadMovimientos();
  }

  async function buscarProducto() {
    const codigo = document.getElementById(`codigo_${tipoMovimiento}`).value;
    if (!codigo) {
      Swal.fire("Error", "Ingrese un código de producto", "error");
      return;
    }

    try {
      const response = await fetch(
        `http://127.0.0.1:8000/productos?codigo=${codigo}`
      );
      if (!response.ok) throw new Error("Producto no encontrado");

      const productos = await response.json();
      if (productos.length === 0) throw new Error("Producto no encontrado");

      const producto = productos[0];

      // Mostrar información del producto encontrado
      Swal.fire({
        title: "Producto encontrado",
        html: `
                    <p><strong>Código:</strong> ${producto.codigo}</p>
                    <p><strong>Nombre:</strong> ${producto.nombre}</p>
                    <p><strong>Stock Actual:</strong></p>
                    <ul>
                        <li>Nuevos: ${producto.cantidad_nuevos}</li>
                        <li>Usados: ${producto.cantidad_usados}</li>
                        <li>Dañados: ${producto.cantidad_danados}</li>
                    </ul>
                `,
        icon: "success",
      });
    } catch (error) {
      Swal.fire("Error", error.message, "error");
    }
  }

  async function handleFormSubmit(e) {
    e.preventDefault();

    const movimientoData = {
      codigo_producto: document.getElementById(`codigo_${tipoMovimiento}`)
        .value,
      tipo: tipoMovimiento,
      cantidad: 0, // Se calculará
      estado: "", // Se determinará
      responsable: document.getElementById(`responsable_${tipoMovimiento}`)
        .value,
      observaciones: document.getElementById(`observaciones_${tipoMovimiento}`)
        .value,
    };

    // Validar cantidades
    const nueva =
      parseInt(
        document.getElementById(`cantidad_nueva_${tipoMovimiento}`).value
      ) || 0;
    const usada =
      parseInt(
        document.getElementById(`cantidad_usada_${tipoMovimiento}`).value
      ) || 0;
    const danada =
      parseInt(
        document.getElementById(`cantidad_danada_${tipoMovimiento}`).value
      ) || 0;

    if (nueva + usada + danada === 0) {
      Swal.fire("Error", "Debe ingresar al menos una cantidad", "error");
      return;
    }

    try {
      // Crear movimiento por cada estado con cantidad > 0
      const movimientos = [];

      if (nueva > 0) {
        movimientos.push({
          ...movimientoData,
          cantidad: nueva,
          estado: "nuevo",
        });
      }

      if (usada > 0) {
        movimientos.push({
          ...movimientoData,
          cantidad: usada,
          estado: "usado",
        });
      }

      if (danada > 0) {
        movimientos.push({
          ...movimientoData,
          cantidad: danada,
          estado: "dañado",
        });
      }

      // Enviar cada movimiento al servidor
      for (const mov of movimientos) {
        const response = await fetch("http://127.0.0.1:8000/movimientos", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(mov),
          credentials: "include",
        });

        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(
            errorData.detail || "Error al registrar el movimiento"
          );
        }
      }

      Swal.fire(
        "Éxito",
        `Registro de ${tipoMovimiento} completado`,
        "success"
      ).then(() => {
        if (movimientoForm) movimientoForm.reset();

        // Restablecer fecha actual
        const fechaInput = document.getElementById(`fecha_${tipoMovimiento}`);
        if (fechaInput) {
          const today = new Date().toISOString().split("T")[0];
          fechaInput.value = today;
        }

        loadMovimientos();
      });
    } catch (error) {
      console.error("Error:", error);
      Swal.fire(
        "Error",
        `No se pudo registrar la ${tipoMovimiento}: ${error.message}`,
        "error"
      );
    }
  }

  async function loadMovimientos(filters = {}) {
    try {
      // Construir URL con filtros
      const params = new URLSearchParams();
      if (filters.fecha) params.append("fecha_inicio", filters.fecha);
      if (filters.codigo) params.append("codigo", filters.codigo);
      if (filters.responsable)
        params.append("responsable", filters.responsable);
      params.append("tipo", tipoMovimiento);

      const response = await fetch(
        `http://127.0.0.1:8000/movimientos?${params.toString()}`
      );
      if (!response.ok) throw new Error("Error al cargar movimientos");

      const movimientos = await response.json();
      renderMovimientos(movimientos);
    } catch (error) {
      console.error("Error:", error);
      Swal.fire("Error", "No se pudieron cargar los movimientos", "error");
    }
  }

  function renderMovimientos(movimientos) {
    const tbody = document.querySelector(`#${tableId} tbody`);
    if (!tbody) return;

    tbody.innerHTML = "";

    movimientos.forEach((mov) => {
      const row = document.createElement("tr");
      row.innerHTML = `
                <td>${new Date(mov.fecha).toLocaleDateString()}</td>
                <td>${mov.codigo_producto}</td>
                <td>${mov.tipo}</td>
                <td>${mov.cantidad}</td>
                <td>${mov.estado}</td>
                <td>${mov.responsable}</td>
                <td>${mov.registrado_por}</td>
                <td>${mov.observaciones || ""}</td>
            `;
      tbody.appendChild(row);
    });
  }

  // Configurar filtros
  const aplicarFiltrosBtn = document.getElementById(
    `aplicarFiltros${
      tipoMovimiento.charAt(0).toUpperCase() + tipoMovimiento.slice(1)
    }`
  );
  const limpiarFiltrosBtn = document.getElementById(
    `limpiarFiltros${
      tipoMovimiento.charAt(0).toUpperCase() + tipoMovimiento.slice(1)
    }`
  );

  if (aplicarFiltrosBtn) {
    aplicarFiltrosBtn.addEventListener("click", aplicarFiltros);
  }

  if (limpiarFiltrosBtn) {
    limpiarFiltrosBtn.addEventListener("click", limpiarFiltros);
  }

  function aplicarFiltros() {
    const filters = {
      fecha: document.getElementById(`fecha_filtro_${tipoMovimiento}`).value,
      codigo: document.getElementById(`codigo_filtro_${tipoMovimiento}`).value,
      responsable: document.getElementById(
        `responsable_filtro_${tipoMovimiento}`
      ).value,
    };
    loadMovimientos(filters);
  }

  function limpiarFiltros() {
    document.getElementById(`fecha_filtro_${tipoMovimiento}`).value = "";
    document.getElementById(`codigo_filtro_${tipoMovimiento}`).value = "";
    document.getElementById(`responsable_filtro_${tipoMovimiento}`).value = "";
    loadMovimientos();
  }
});
