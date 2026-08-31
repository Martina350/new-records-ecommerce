function inicializarAplicacion() {
  inicializarSidebar();
  inicializarToasts();
  inicializarNavLanding();
  inicializarModalesAuth();
  inicializarValidacionesAuth();
  inicializarCustomSelects();
  configurarFormularioTarjeta();
  inicializarResumenCarrito();
  inicializarCheckoutHorizontal();
  inicializarModalesPedidosMovil();
  inicializarToggleInfoSeguridad();
  inicializarDropdownAdmin();
  inicializarUploaderPreviewAdmin();
  inicializarGraficosReportes();
  inicializarCargarMasDiscosAdmin();
  inicializarCargarMasProductosCatalogo();
}

function sincronizarClaseBody(evento) {
  const detalle = evento.detail;
  if (
    !detalle ||
    !detalle.shouldSwap ||
    detalle.target !== document.body ||
    !detalle.xhr ||
    !detalle.xhr.responseText.includes('<body')
  ) return;

  const documentoNuevo = new DOMParser().parseFromString(
    detalle.xhr.responseText,
    'text/html'
  );
  if (documentoNuevo.body) {
    document.body.className = documentoNuevo.body.className;
  }
}

function mostrarTransicionClasica() {
  if (document.body) document.body.classList.add('navegacion-clasica');
}

function inicializarRespaldoNavegacion() {
  if (document.documentElement.dataset.respaldoNavegacion === 'activo') return;
  document.documentElement.dataset.respaldoNavegacion = 'activo';

  document.addEventListener('click', (evento) => {
    if (window.htmx || evento.defaultPrevented || evento.button !== 0) return;
    if (evento.metaKey || evento.ctrlKey || evento.shiftKey || evento.altKey) return;

    const enlace = evento.target.closest('a[href]');
    if (!enlace || enlace.hasAttribute('download')) return;
    if (enlace.target && enlace.target !== '_self') return;

    const destino = new URL(enlace.href, window.location.href);
    const esAnclaLocal =
      destino.pathname === window.location.pathname &&
      destino.search === window.location.search &&
      destino.hash;

    if (destino.origin === window.location.origin && !esAnclaLocal) {
      mostrarTransicionClasica();
    }
  });

  document.addEventListener('submit', (evento) => {
    if (window.htmx || evento.defaultPrevented) return;
    const formulario = evento.target;
    if (!(formulario instanceof HTMLFormElement)) return;
    if (formulario.target && formulario.target !== '_self') return;
    mostrarTransicionClasica();
  });

  window.addEventListener('pageshow', () => {
    if (document.body) document.body.classList.remove('navegacion-clasica');
  });
}

document.addEventListener('DOMContentLoaded', () => {
  inicializarAplicacion();
  inicializarRespaldoNavegacion();
});

document.addEventListener('htmx:beforeSwap', sincronizarClaseBody);
document.addEventListener('htmx:afterSettle', inicializarAplicacion);

/**
 * Control del Menú Móvil en la Cabecera de Inicio (Landing)
 */
function inicializarNavLanding() {
  const btnToggle = document.getElementById('btnToggleNavLanding');
  const navMovil = document.getElementById('navMovilLanding');
  if (!btnToggle || !navMovil) return;

  btnToggle.addEventListener('click', () => {
    const abierto = navMovil.classList.toggle('abierto');
    btnToggle.setAttribute('aria-expanded', String(abierto));
  });

  navMovil.querySelectorAll('a').forEach((enlace) => {
    enlace.addEventListener('click', () => {
      navMovil.classList.remove('abierto');
      btnToggle.setAttribute('aria-expanded', 'false');
    });
  });
}

// Delegación global directa para acordeones del sidebar (inmune a re-renderizaciones)
document.addEventListener('click', (evento) => {
  const btn = evento.target.closest('.btn-acordeon-sidebar');
  if (!btn) return;

  const submodulo = btn.closest('.submodulo-sidebar');
  if (!submodulo) return;

  evento.preventDefault();
  evento.stopPropagation();
  const estaAbierto = submodulo.classList.toggle('abierto');
  btn.setAttribute('aria-expanded', String(estaAbierto));
});

/**
 * Control del Sidebar Lateral: Colapsar/Expandir en Desktop,
 * Slide-over en Móvil, Acordeones Jerárquicos y Auto-expansión.
 */
function inicializarSidebar() {
  const sidebar = document.getElementById('sidebar');
  if (!sidebar) return;

  const btnMobileToggle = document.getElementById('btnToggleSidebarMobile');
  const btnMobileClose = document.getElementById('btnCerrarSidebarMobile');
  const backdrop = document.getElementById('sidebarBackdrop');

  // Apertura y Cierre en Dispositivos Móviles
  const toggleMobileSidebar = (abrir) => {
    if (abrir) {
      document.querySelectorAll('.custom-select-contenedor.abierto').forEach((c) => {
        c.classList.remove('abierto');
        c.querySelector('.custom-select-boton')?.setAttribute('aria-expanded', 'false');
      });
    }
    sidebar.classList.toggle('abierto-movil', abrir);
    if (backdrop) backdrop.classList.toggle('visible', abrir);
    if (btnMobileToggle) btnMobileToggle.setAttribute('aria-expanded', String(abrir));
    document.body.style.overflow = abrir ? 'hidden' : '';
  };

  if (btnMobileToggle && !btnMobileToggle.dataset.sidebarInit) {
    btnMobileToggle.dataset.sidebarInit = 'true';
    btnMobileToggle.addEventListener('click', () => {
      toggleMobileSidebar(!sidebar.classList.contains('abierto-movil'));
    });
  }

  if (btnMobileClose && !btnMobileClose.dataset.sidebarInit) {
    btnMobileClose.dataset.sidebarInit = 'true';
    btnMobileClose.addEventListener('click', () => toggleMobileSidebar(false));
  }

  if (backdrop && !backdrop.dataset.sidebarInit) {
    backdrop.dataset.sidebarInit = 'true';
    backdrop.addEventListener('click', () => toggleMobileSidebar(false));
  }

  // Cerrar sidebar móvil con tecla Escape
  document.removeEventListener('keydown', manejarEscapeSidebar);
  document.addEventListener('keydown', manejarEscapeSidebar);

  // Cerrar al pulsar un enlace de navegación en móvil
  sidebar.querySelectorAll('a').forEach((enlace) => {
    if (enlace.dataset.linkMovilInit) return;
    enlace.dataset.linkMovilInit = 'true';
    enlace.addEventListener('click', () => {
      if (window.innerWidth < 1024) {
        toggleMobileSidebar(false);
      }
    });
  });

  // Auto-expansión del submenú activo basado en la ruta actual
  const subitems = sidebar.querySelectorAll('.submodulo-sidebar');
  const rutaActual = window.location.pathname;

  subitems.forEach((submodulo) => {
    const enlaceActivo = submodulo.querySelector('.enlace-subitem.activo') ||
      Array.from(submodulo.querySelectorAll('.enlace-subitem')).some((a) => {
        const href = a.getAttribute('href');
        return href && (rutaActual === href || (href !== '/' && rutaActual.startsWith(href)));
      });

    if (enlaceActivo) {
      submodulo.classList.add('abierto');
      const btn = submodulo.querySelector('.btn-acordeon-sidebar');
      if (btn) btn.setAttribute('aria-expanded', 'true');
    }
  });
}

function manejarEscapeSidebar(evento) {
  const sidebar = document.getElementById('sidebar');
  if (evento.key !== 'Escape' || !sidebar?.classList.contains('abierto-movil')) return;

  sidebar.classList.remove('abierto-movil');
  document.getElementById('sidebarBackdrop')?.classList.remove('visible');
  document.getElementById('btnToggleSidebarMobile')?.setAttribute('aria-expanded', 'false');
  document.body.style.overflow = '';
}

/**
 * Sistema de Notificaciones Toast Flotantes con Auto-cierre
 */
function inicializarToasts() {
  const toasts = document.querySelectorAll('.toast-alerta');
  
  toasts.forEach((toast) => {
    const cerrar = () => {
      toast.classList.add('toast-salida');
      toast.addEventListener('animationend', () => {
        toast.remove();
      }, { once: true });
    };

    const btnCerrar = toast.querySelector('.btn-cerrar-toast');
    if (btnCerrar) {
      btnCerrar.addEventListener('click', cerrar);
    }

    // Auto-cierre después de 4.5 segundos
    setTimeout(() => {
      if (toast.isConnected && !toast.classList.contains('toast-salida')) {
        cerrar();
      }
    }, 4500);
  });
}

function configurarFormularioTarjeta() {
  const formularioTarjeta = document.getElementById('form-tarjeta');
  if (!formularioTarjeta) return;

  const numero = document.getElementById('numero');
  const mes = document.getElementById('mes_vencimiento');
  const anio = document.getElementById('anio_vencimiento');

  numero.addEventListener('input', () => {
    const digitos = numero.value.replace(/\D/g, '').slice(0, 19);
    numero.value = digitos.replace(/(.{4})/g, '$1 ').trim();
    numero.setCustomValidity('');
  });

  formularioTarjeta.addEventListener('submit', (evento) => {
    const digitos = numero.value.replace(/\D/g, '');
    numero.setCustomValidity(
      validarNumeroLuhn(digitos) ? '' : 'Ingresa un número de tarjeta válido.'
    );

    const anioActual = Number(formularioTarjeta.dataset.anioActual);
    const mesActual = Number(formularioTarjeta.dataset.mesActual);
    const mesIngresado = Number(mes.value);
    const anioIngresado = Number(anio.value);
    const vencimientoValido =
      mesIngresado >= 1 &&
      mesIngresado <= 12 &&
      (anioIngresado > anioActual ||
        (anioIngresado === anioActual && mesIngresado >= mesActual)) &&
      anioIngresado <= anioActual + 20;

    anio.setCustomValidity(
      vencimientoValido ? '' : 'La tarjeta está vencida o su fecha no es válida.'
    );

    if (!formularioTarjeta.checkValidity()) {
      evento.preventDefault();
      formularioTarjeta.reportValidity();
    }
  }, { capture: true });
}

function validarNumeroLuhn(numero) {
  if (!/^\d{13,19}$/.test(numero)) return false;

  let total = 0;
  [...numero].reverse().forEach((caracter, indice) => {
    let digito = Number(caracter);
    if (indice % 2 === 1) {
      digito *= 2;
      if (digito > 9) digito -= 9;
    }
    total += digito;
  });
  return total % 10 === 0;
}

function validarFormulario() {
  let esValido = true;

  const nombre = document.getElementById('name');
  const valorNombre = nombre.value.trim();

  if (valorNombre === '' || valorNombre.length < 3) {
    nombre.classList.add('no-valido');
    mostrarError('nameError', valorNombre === '' ? 'El nombre es obligatorio.' : 'El nombre debe tener al menos 3 caracteres.');
    esValido = false;
  } else {
    nombre.classList.remove('no-valido');
    ocultarError('nameError');
  }

  const ciudad = document.getElementById('city');
  const valorCiudad = ciudad.value.trim();

  if (valorCiudad === '') {
    ciudad.classList.add('no-valido');
    mostrarError('cityError', 'La ciudad es obligatoria.');
    esValido = false;
  } else {
    ciudad.classList.remove('no-valido');
    ocultarError('cityError');
  }

  const email = document.getElementById('email');
  const valorEmail = email.value.trim();
  const regexEmail = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

  if (valorEmail === '') {
    email.classList.add('no-valido');
    mostrarError('emailError', 'El email es obligatorio.');
    esValido = false;
  } else if (!regexEmail.test(valorEmail)) {
    email.classList.add('no-valido');
    mostrarError('emailError', 'Introduce un email válido.');
    esValido = false;
  } else {
    email.classList.remove('no-valido');
    ocultarError('emailError');
  }

  const asunto = document.getElementById('subject');
  const valorAsunto = asunto.value.trim();

  if (valorAsunto === '') {
    asunto.classList.add('no-valido');
    mostrarError('subjectError', 'El asunto es obligatorio.');
    esValido = false;
  } else {
    asunto.classList.remove('no-valido');
    ocultarError('subjectError');
  }

  const descripcion = document.getElementById('description');
  const valorDescripcion = descripcion.value.trim();

  if (valorDescripcion === '' || valorDescripcion.length < 10) {
    descripcion.classList.add('no-valido');
    mostrarError('descriptionError', valorDescripcion === '' ? 'El mensaje es obligatorio.' : 'La descripción debe tener al menos 10 caracteres.');
    esValido = false;
  } else {
    descripcion.classList.remove('no-valido');
    ocultarError('descriptionError');
  }

  return esValido;
}

function mostrarError(idElemento, mensaje) {
  const elemento = document.getElementById(idElemento);
  if (elemento) {
    elemento.textContent = mensaje;
    elemento.classList.add('visible');
  }
}

function ocultarError(idElemento) {
  const elemento = document.getElementById(idElemento);
  if (elemento) {
    elemento.textContent = '';
    elemento.classList.remove('visible');
  }
}

function mostrarExito(formulario) {
  const mensajeExito = document.getElementById('successMessage');
  if (mensajeExito) mensajeExito.classList.add('visible');
  formulario.reset();
  formulario.querySelectorAll('input, textarea').forEach((input) => input.classList.remove('no-valido'));
  ocultarError('nameError');
  ocultarError('cityError');
  ocultarError('emailError');
  ocultarError('subjectError');
  ocultarError('descriptionError');
}

/**
 * Control de Modales de Autenticación con Desenfoque de Pantalla de Inicio
 */
function inicializarModalesAuth() {
  const modalLogin = document.getElementById('modalLoginOverlay');
  const modalRegistro = document.getElementById('modalRegistroOverlay');
  const seccionInicio = document.getElementById('seccionInicio');

  const abrirModal = (modal) => {
    if (!modal) return;
    if (modalLogin) modalLogin.classList.remove('activo');
    if (modalRegistro) modalRegistro.classList.remove('activo');
    modal.classList.add('activo');
    if (seccionInicio) seccionInicio.classList.add('desenfocado');
  };

  const cerrarModales = () => {
    if (modalLogin) modalLogin.classList.remove('activo');
    if (modalRegistro) modalRegistro.classList.remove('activo');
    if (seccionInicio) seccionInicio.classList.remove('desenfocado');
  };

  const btnsHeaderLogin = document.querySelectorAll('.btn-abrir-login, .enlace-login-header, #btnHeaderLogin');
  btnsHeaderLogin.forEach((btn) => {
    btn.addEventListener('click', (e) => {
      if (modalLogin && seccionInicio) {
        e.preventDefault();
        abrirModal(modalLogin);
      }
    });
  });

  const btnsHeroRegistro = document.querySelectorAll('.btn-abrir-registro, #btnHeroRegistro');
  btnsHeroRegistro.forEach((btn) => {
    btn.addEventListener('click', (e) => {
      if (modalRegistro && seccionInicio) {
        e.preventDefault();
        abrirModal(modalRegistro);
      }
    });
  });

  // Botones de cierre X
  const btnCerrarLogin = document.getElementById('btnCerrarLoginModal');
  const btnCerrarRegistro = document.getElementById('btnCerrarRegistroModal');
  if (btnCerrarLogin) btnCerrarLogin.addEventListener('click', cerrarModales);
  if (btnCerrarRegistro) btnCerrarRegistro.addEventListener('click', cerrarModales);

  // Cerrar al dar clic en el backdrop exterior
  [modalLogin, modalRegistro].forEach((modal) => {
    if (!modal) return;
    modal.addEventListener('click', (e) => {
      if (e.target === modal) {
        cerrarModales();
      }
    });
  });

  // Alternar entre Login y Registro dentro del Modal
  document.querySelectorAll('.btn-cambiar-a-registro').forEach((btn) => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      abrirModal(modalRegistro);
    });
  });

  document.querySelectorAll('.btn-cambiar-a-login').forEach((btn) => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      abrirModal(modalLogin);
    });
  });

  // Cerrar con Escape sin acumular listeners tras cada navegación parcial.
  document.removeEventListener('keydown', manejarEscapeModales);
  document.addEventListener('keydown', manejarEscapeModales);
}

function manejarEscapeModales(evento) {
  if (evento.key !== 'Escape') return;

  document.getElementById('modalLoginOverlay')?.classList.remove('activo');
  document.getElementById('modalRegistroOverlay')?.classList.remove('activo');
  document.getElementById('seccionInicio')?.classList.remove('desenfocado');
}

/**
 * Validaciones dinámicas e interactivas debajo de cada campo
 * para los formularios de Registro y Login (sin popups ni toasts).
 */
function inicializarValidacionesAuth() {
  const formulariosRegistro = document.querySelectorAll('#formRegistro, #formRegistroLanding');
  formulariosRegistro.forEach((form) => {
    const inputNombre = form.querySelector('input[name="nombre"]');
    const inputEmail = form.querySelector('input[name="email"]');
    const inputPassword = form.querySelector('input[name="password"]');
    const inputConfirmar = form.querySelector('input[name="confirmar_password"]');

    const getErrorSpan = (input) => {
      if (!input) return null;
      const grupo = input.closest('.grupo-formulario');
      return grupo ? grupo.querySelector('.mensaje-error') : null;
    };

    const spanNombreError = getErrorSpan(inputNombre);
    const spanEmailError = getErrorSpan(inputEmail);
    const spanPasswordError = getErrorSpan(inputPassword);
    const spanConfirmarError = getErrorSpan(inputConfirmar);

    const setFieldError = (input, span, mensaje) => {
      if (input) input.classList.add('no-valido');
      if (span) {
        span.textContent = mensaje;
        span.classList.add('visible');
      }
    };

    const clearFieldError = (input, span) => {
      if (input) input.classList.remove('no-valido');
      if (span) {
        span.textContent = '';
        span.classList.remove('visible');
      }
    };

    const validarNombre = () => {
      if (!inputNombre) return true;
      const valor = inputNombre.value.trim();
      if (!valor) {
        setFieldError(inputNombre, spanNombreError, 'El nombre completo es un campo obligatorio.');
        return false;
      }
      if (valor.length < 2 || valor.length > 100) {
        setFieldError(inputNombre, spanNombreError, 'El nombre debe contener entre 2 y 100 caracteres.');
        return false;
      }
      clearFieldError(inputNombre, spanNombreError);
      return true;
    };

    const validarEmail = () => {
      if (!inputEmail) return true;
      const valor = inputEmail.value.trim();
      const regexEmail = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      if (!valor) {
        setFieldError(inputEmail, spanEmailError, 'El correo es un campo obligatorio.');
        return false;
      }
      if (!regexEmail.test(valor)) {
        setFieldError(inputEmail, spanEmailError, 'El correo debe ser un correo válido.');
        return false;
      }
      clearFieldError(inputEmail, spanEmailError);
      return true;
    };

    const validarPassword = () => {
      if (!inputPassword) return true;
      const valor = inputPassword.value;
      if (!valor) {
        setFieldError(inputPassword, spanPasswordError, 'La contraseña es un campo obligatorio.');
        return false;
      }
      if (valor.length < 8) {
        setFieldError(inputPassword, spanPasswordError, 'La contraseña debe tener mínimo 8 caracteres.');
        return false;
      }
      clearFieldError(inputPassword, spanPasswordError);
      return true;
    };

    const validarConfirmacion = () => {
      if (!inputConfirmar || !inputPassword) return true;
      const pass = inputPassword.value;
      const confirm = inputConfirmar.value;
      if (!confirm) {
        setFieldError(inputConfirmar, spanConfirmarError, 'Confirmar contraseña es un campo obligatorio.');
        return false;
      }
      if (pass !== confirm) {
        setFieldError(inputConfirmar, spanConfirmarError, 'La contraseña debe coincidir.');
        return false;
      }
      clearFieldError(inputConfirmar, spanConfirmarError);
      return true;
    };

    if (inputNombre) {
      inputNombre.addEventListener('input', validarNombre);
      inputNombre.addEventListener('blur', validarNombre);
    }
    if (inputEmail) {
      inputEmail.addEventListener('input', validarEmail);
      inputEmail.addEventListener('blur', validarEmail);
    }
    if (inputPassword) {
      inputPassword.addEventListener('input', () => {
        validarPassword();
        if (inputConfirmar && inputConfirmar.value) validarConfirmacion();
      });
      inputPassword.addEventListener('blur', validarPassword);
    }
    if (inputConfirmar) {
      inputConfirmar.addEventListener('input', validarConfirmacion);
      inputConfirmar.addEventListener('blur', validarConfirmacion);
    }

    form.addEventListener('submit', (e) => {
      const v1 = validarNombre();
      const v2 = validarEmail();
      const v3 = validarPassword();
      const v4 = validarConfirmacion();
      if (!v1 || !v2 || !v3 || !v4) {
        e.preventDefault();
      }
    }, { capture: true });
  });

  const formulariosLogin = document.querySelectorAll('#formLogin, #formLoginLanding');
  formulariosLogin.forEach((form) => {
    const inputEmail = form.querySelector('input[name="email"]');
    const inputPassword = form.querySelector('input[name="password"]');

    const getErrorSpan = (input) => {
      if (!input) return null;
      const grupo = input.closest('.grupo-formulario');
      return grupo ? grupo.querySelector('.mensaje-error') : null;
    };

    const spanEmailError = getErrorSpan(inputEmail);
    const spanPasswordError = getErrorSpan(inputPassword);

    const setFieldError = (input, span, mensaje) => {
      if (input) input.classList.add('no-valido');
      if (span) {
        span.textContent = mensaje;
        span.classList.add('visible');
      }
    };

    const clearFieldError = (input, span) => {
      if (input) input.classList.remove('no-valido');
      if (span) {
        span.textContent = '';
        span.classList.remove('visible');
      }
    };

    const validarLoginEmail = () => {
      if (!inputEmail) return true;
      const valor = inputEmail.value.trim();
      const regexEmail = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      if (!valor) {
        setFieldError(inputEmail, spanEmailError, 'El correo electrónico es un campo obligatorio.');
        return false;
      }
      if (!regexEmail.test(valor)) {
        setFieldError(inputEmail, spanEmailError, 'El correo debe ser un correo válido.');
        return false;
      }
      clearFieldError(inputEmail, spanEmailError);
      return true;
    };

    const validarLoginPassword = () => {
      if (!inputPassword) return true;
      const valor = inputPassword.value;
      if (!valor) {
        setFieldError(inputPassword, spanPasswordError, 'La contraseña es un campo obligatorio.');
        return false;
      }
      clearFieldError(inputPassword, spanPasswordError);
      return true;
    };

    if (inputEmail) {
      inputEmail.addEventListener('input', validarLoginEmail);
      inputEmail.addEventListener('blur', validarLoginEmail);
    }
    if (inputPassword) {
      inputPassword.addEventListener('input', validarLoginPassword);
      inputPassword.addEventListener('blur', validarLoginPassword);
    }

    form.addEventListener('submit', (e) => {
      const v1 = validarLoginEmail();
      const v2 = validarLoginPassword();
      if (!v1 || !v2) {
        e.preventDefault();
      }
    }, { capture: true });
  });
}

/**
 * Sistema de Selects y Desplegables Personalizados con Estilos Neón / Dark
 */
function inicializarCustomSelects() {
  const selects = document.querySelectorAll('select.select-custom, .contenedor-select-estilizado select, .campo-formulario select, select.select-filtro-categoria, select.entrada-formulario');

  selects.forEach((select) => {
    if (select.dataset.customized === 'true') {
      const wrapper = select.closest('.custom-select-wrapper');
      if (wrapper) {
        const label = wrapper.querySelector('.custom-select-label');
        const selectedOption = select.options[select.selectedIndex];
        if (label && selectedOption) {
          label.textContent = selectedOption.textContent.trim();
        }
      }
      return;
    }

    select.dataset.customized = 'true';

    // Crear Contenedor Wrapper
    const wrapper = document.createElement('div');
    wrapper.className = 'custom-select-wrapper';
    select.parentNode.insertBefore(wrapper, select);
    wrapper.appendChild(select);

    // Botón Desplegable (Trigger)
    const trigger = document.createElement('button');
    trigger.type = 'button';
    trigger.className = 'custom-select-trigger';
    trigger.setAttribute('aria-haspopup', 'listbox');
    trigger.setAttribute('aria-expanded', 'false');

    const selectedOption = select.options[select.selectedIndex] || select.options[0];
    const triggerLabel = document.createElement('span');
    triggerLabel.className = 'custom-select-label';
    triggerLabel.textContent = selectedOption ? selectedOption.textContent.trim() : '';

    const triggerIcon = document.createElement('span');
    triggerIcon.className = 'material-symbols-outlined icono-select-flecha';
    triggerIcon.setAttribute('aria-hidden', 'true');
    triggerIcon.textContent = 'expand_more';

    trigger.appendChild(triggerLabel);
    trigger.appendChild(triggerIcon);
    wrapper.appendChild(trigger);

    // Menú de Opciones Flotante
    const menu = document.createElement('div');
    menu.className = 'custom-select-menu';
    menu.setAttribute('role', 'listbox');

    const renderOptions = () => {
      menu.innerHTML = '';
      Array.from(select.options).forEach((opt, idx) => {
        const optionEl = document.createElement('div');
        optionEl.className = `custom-select-option ${opt.selected ? 'seleccionado' : ''}`;
        optionEl.setAttribute('role', 'option');
        optionEl.setAttribute('data-value', opt.value);
        if (opt.disabled) optionEl.classList.add('deshabilitado');

        const optionText = document.createElement('span');
        optionText.textContent = opt.textContent.trim();
        optionEl.appendChild(optionText);

        if (opt.selected) {
          const checkIcon = document.createElement('span');
          checkIcon.className = 'material-symbols-outlined icono-check';
          checkIcon.textContent = 'check';
          optionEl.appendChild(checkIcon);
        }

        optionEl.addEventListener('click', (e) => {
          e.stopPropagation();
          if (opt.disabled) return;

          select.selectedIndex = idx;
          triggerLabel.textContent = opt.textContent.trim();

          menu.querySelectorAll('.custom-select-option').forEach((el) => {
            el.classList.remove('seleccionado');
            const check = el.querySelector('.icono-check');
            if (check) check.remove();
          });
          optionEl.classList.add('seleccionado');
          const checkIcon = document.createElement('span');
          checkIcon.className = 'material-symbols-outlined icono-check';
          checkIcon.textContent = 'check';
          optionEl.appendChild(checkIcon);

          wrapper.classList.remove('abierto');
          trigger.setAttribute('aria-expanded', 'false');

          select.dispatchEvent(new Event('change', { bubbles: true }));
          select.dispatchEvent(new Event('input', { bubbles: true }));

          if (typeof select.onchange === 'function') {
            select.onchange();
          }
        });

        menu.appendChild(optionEl);
      });
    };

    renderOptions();
    wrapper.appendChild(menu);

    trigger.addEventListener('click', (e) => {
      e.stopPropagation();
      const estaAbierto = wrapper.classList.contains('abierto');
      document.querySelectorAll('.custom-select-wrapper.abierto').forEach((w) => {
        if (w !== wrapper) {
          w.classList.remove('abierto');
          const tr = w.querySelector('.custom-select-trigger');
          if (tr) tr.setAttribute('aria-expanded', 'false');
        }
      });

      if (estaAbierto) {
        wrapper.classList.remove('abierto');
        trigger.setAttribute('aria-expanded', 'false');
      } else {
        renderOptions();
        wrapper.classList.add('abierto');
        trigger.setAttribute('aria-expanded', 'true');
      }
    });

    select.addEventListener('change', () => {
      const actualOpt = select.options[select.selectedIndex];
      if (actualOpt) {
        triggerLabel.textContent = actualOpt.textContent.trim();
        renderOptions();
      }
    });
  });
}

document.addEventListener('click', () => {
  document.querySelectorAll('.custom-select-wrapper.abierto').forEach((w) => {
    w.classList.remove('abierto');
    const tr = w.querySelector('.custom-select-trigger');
    if (tr) tr.setAttribute('aria-expanded', 'false');
  });
});

document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') {
    document.querySelectorAll('.custom-select-wrapper.abierto').forEach((w) => {
      w.classList.remove('abierto');
      const tr = w.querySelector('.custom-select-trigger');
      if (tr) tr.setAttribute('aria-expanded', 'false');
    });
  }
});

/**
 * Control del Panel Desplegable (Slide-Over / Modal) de Resumen de Pedido
 */
function inicializarResumenCarrito() {
  const btnToggle = document.getElementById('btnToggleResumenPedido');
  const btnAbrirBottom = document.getElementById('btnAbrirResumenBottom');
  const btnCerrar = document.getElementById('btnCerrarResumenPedido');
  const btnContinuar = document.getElementById('btnContinuarComprandoPanel');
  const panel = document.getElementById('panelResumenPedido');
  const overlay = document.getElementById('overlayResumenPedido');

  if (!panel || !overlay) return;

  const abrirResumen = () => {
    panel.classList.add('abierto');
    overlay.classList.add('abierto');
    panel.setAttribute('aria-hidden', 'false');
    overlay.setAttribute('aria-hidden', 'false');
    if (btnToggle) btnToggle.setAttribute('aria-expanded', 'true');
    document.body.style.overflow = 'hidden';
  };

  const cerrarResumen = () => {
    panel.classList.remove('abierto');
    overlay.classList.remove('abierto');
    panel.setAttribute('aria-hidden', 'true');
    overlay.setAttribute('aria-hidden', 'true');
    if (btnToggle) btnToggle.setAttribute('aria-expanded', 'false');
    document.body.style.overflow = '';
  };

  const toggleResumen = () => {
    if (panel.classList.contains('abierto')) {
      cerrarResumen();
    } else {
      abrirResumen();
    }
  };

  if (btnToggle) btnToggle.addEventListener('click', toggleResumen);
  if (btnAbrirBottom) btnAbrirBottom.addEventListener('click', abrirResumen);
  if (btnCerrar) btnCerrar.addEventListener('click', cerrarResumen);
  if (btnContinuar) btnContinuar.addEventListener('click', cerrarResumen);
  overlay.addEventListener('click', cerrarResumen);

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && panel.classList.contains('abierto')) {
      cerrarResumen();
    }
  });
}

/**
 * Control Interactivo de Selección de Tarjetas en Checkout Horizontal
 */
function inicializarCheckoutHorizontal() {
  const radios = document.querySelectorAll('.radio-metodo-real');
  if (!radios.length) return;

  radios.forEach((radio) => {
    radio.addEventListener('change', () => {
      document.querySelectorAll('.metodo-pago-tarjeta-box').forEach((box) => {
        box.classList.remove('seleccionado');
      });
      const boxPadre = radio.closest('.metodo-pago-tarjeta-label')?.querySelector('.metodo-pago-tarjeta-box');
      if (boxPadre && radio.checked) {
        boxPadre.classList.add('seleccionado');
      }
    });
  });
}

/**
 * Control del Modal de Detalle de Pedidos en Vista Móvil (< 768px)
 */
function inicializarModalesPedidosMovil() {
  const cards = document.querySelectorAll('.card-pedido-movil-compacta');
  if (!cards.length) return;

  const cerrarTodosLosModales = () => {
    document.querySelectorAll('.modal-pedido-overlay.abierto').forEach((modal) => {
      modal.classList.remove('abierto');
      modal.setAttribute('aria-hidden', 'true');
    });
    document.body.classList.remove('modal-pedido-abierto');
  };

  cards.forEach((card) => {
    const modalId = card.dataset.pedidoModal;
    if (!modalId) return;
    const modal = document.getElementById(modalId);
    if (!modal) return;

    const abrirModal = (e) => {
      if (e && e.target && e.target.closest('a')) return;
      cerrarTodosLosModales();
      modal.classList.add('abierto');
      modal.setAttribute('aria-hidden', 'false');
      document.body.classList.add('modal-pedido-abierto');
    };

    card.addEventListener('click', (e) => {
      abrirModal(e);
    });

    card.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        abrirModal(e);
      }
    });

    const btnAbrir = card.querySelector('.btn-abrir-modal-pedido');
    if (btnAbrir) {
      btnAbrir.addEventListener('click', (e) => {
        e.stopPropagation();
        abrirModal(e);
      });
    }

    // Botones de cerrar dentro del modal
    modal.querySelectorAll('.btn-cerrar-modal-pedido').forEach((btn) => {
      btn.addEventListener('click', (e) => {
        e.stopPropagation();
        cerrarTodosLosModales();
      });
    });

    // Cerrar al hacer click fuera del diálogo
    modal.addEventListener('click', (e) => {
      if (e.target === modal) {
        cerrarTodosLosModales();
      }
    });
  });

  // Cerrar con Escape
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      cerrarTodosLosModales();
    }
  });
}

/**
 * Control Interactivo y Accesible del Dropdown de Perfil en el Dashboard de Administración
 */
function inicializarDropdownAdmin() {
  const dropdown = document.getElementById('dropdownUsuarioAdmin');
  if (!dropdown) return;

  const btnPerfil = document.getElementById('btnPerfilUsuario');
  const menu = document.getElementById('menuDropdownAdmin');
  if (!btnPerfil || !menu) return;

  // Evitar vincular múltiples veces los mismos listeners si HTMX re-ejecuta
  if (dropdown.dataset.inicializado === 'true') return;
  dropdown.dataset.inicializado = 'true';

  const abrirMenu = () => {
    btnPerfil.setAttribute('aria-expanded', 'true');
    menu.classList.add('abierto');
  };

  const cerrarMenu = () => {
    btnPerfil.setAttribute('aria-expanded', 'false');
    menu.classList.remove('abierto');
  };

  btnPerfil.addEventListener('click', (e) => {
    e.stopPropagation();
    const estaAbierto = btnPerfil.getAttribute('aria-expanded') === 'true';
    if (estaAbierto) {
      cerrarMenu();
    } else {
      abrirMenu();
    }
  });

  document.addEventListener('click', (e) => {
    if (!dropdown.contains(e.target)) {
      cerrarMenu();
    }
  });

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && btnPerfil.getAttribute('aria-expanded') === 'true') {
      cerrarMenu();
      btnPerfil.focus();
    }
  });
}

/**
 * Controlador de Vista Previa de Imagen con Soporte Drag & Drop y Remoción
 */
function inicializarUploaderPreviewAdmin() {
  const panel = document.getElementById('panelCargaImagen');
  if (!panel) return;

  const inputValor = document.getElementById('inputImagenValor');
  const inputArchivo = document.getElementById('inputArchivoImagen');
  const zonaDrop = document.getElementById('zonaDropArchivos');
  const imgElemento = document.getElementById('imagenPrevisualizada');
  const placeholder = document.getElementById('placeholderPreviewArte');
  const btnEliminar = document.getElementById('btnEliminarImagen');

  if (!inputValor || !inputArchivo || !zonaDrop || !imgElemento || !placeholder || !btnEliminar) {
    return;
  }

  // Evitar duplicación de listeners en ciclos HTMX
  if (panel.dataset.inicializado === 'true') return;
  panel.dataset.inicializado = 'true';

  const mostrarImagen = (urlOData) => {
    imgElemento.src = urlOData;
    imgElemento.classList.remove('oculto');
    placeholder.classList.add('oculto');
    btnEliminar.classList.remove('oculto');
    inputValor.value = urlOData;
  };

  const limpiarImagen = () => {
    imgElemento.src = '';
    imgElemento.classList.add('oculto');
    placeholder.classList.remove('oculto');
    btnEliminar.classList.add('oculto');
    inputValor.value = '';
    inputArchivo.value = '';
  };

  const procesarArchivo = (archivo) => {
    if (!archivo || !archivo.type.startsWith('image/')) {
      alert('Por favor, selecciona un archivo de imagen válido (JPG, PNG, WEBP).');
      return;
    }

    const lector = new FileReader();
    lector.onload = (e) => {
      if (e.target && e.target.result) {
        mostrarImagen(e.target.result);
      }
    };
    lector.readAsDataURL(archivo);
  };

  inputArchivo.addEventListener('change', (e) => {
    if (e.target.files && e.target.files[0]) {
      procesarArchivo(e.target.files[0]);
    }
  });

  ['dragenter', 'dragover'].forEach((nombreEvento) => {
    zonaDrop.addEventListener(nombreEvento, (e) => {
      e.preventDefault();
      e.stopPropagation();
      zonaDrop.classList.add('drag-activo');
    });
  });

  ['dragleave', 'drop'].forEach((nombreEvento) => {
    zonaDrop.addEventListener(nombreEvento, (e) => {
      e.preventDefault();
      e.stopPropagation();
      zonaDrop.classList.remove('drag-activo');
    });
  });

  zonaDrop.addEventListener('drop', (e) => {
    const archivos = e.dataTransfer.files;
    if (archivos && archivos.length > 0) {
      procesarArchivo(archivos[0]);
    }
  });

  btnEliminar.addEventListener('click', (e) => {
    e.preventDefault();
    limpiarImagen();
  });
}

/**
 * Inicialización y Renderizado Dinámico del Gráfico de Pastel / Donut
 */
function inicializarGraficosReportes() {
  const pieChart = document.getElementById('graficoPieCategorias');
  if (!pieChart) return;

  const items = document.querySelectorAll('.item-leyenda-pie');
  if (!items.length) return;

  // Paleta armónica de colores Dark Cyberpunk
  const paletaColores = [
    '#8a2ce2', // Violeta Neón principal
    '#00FF41', // Verde Neón acento
    '#38bdf8', // Cyan eléctrico
    '#f59e0b', // Ámbar / Dorado
    '#ec4899', // Rosa Neón
    '#a855f7', // Púrpura suave
    '#10b981', // Esmeralda
    '#f43f5e'  // Coral
  ];

  const segmentos = [];
  let acumulado = 0;

  items.forEach((item, index) => {
    const porcentaje = parseFloat(item.dataset.porcentaje) || 0;
    const color = paletaColores[index % paletaColores.length];
    
    const inicio = acumulado;
    const fin = acumulado + porcentaje;
    segmentos.push(`${color} ${inicio}% ${fin}%`);
    acumulado = fin;

    // Asignar color al swatch de la leyenda
    const swatch = item.querySelector('.pie-swatch');
    if (swatch) {
      swatch.style.backgroundColor = color;
      swatch.style.color = color;
    }
  });

  if (segmentos.length > 0) {
    pieChart.style.background = `conic-gradient(${segmentos.join(', ')})`;
  }
}

/**
 * Toggle Interactivo de Información de Seguridad en Métodos de Pago
 */
function inicializarToggleInfoSeguridad() {
  const btnToggle = document.getElementById('btnToggleInfoSeguridad');
  const panelSeguridad = document.getElementById('panelInfoSeguridad');
  if (!btnToggle || !panelSeguridad) return;

  btnToggle.addEventListener('click', (e) => {
    e.preventDefault();
    const estaVisible = panelSeguridad.classList.toggle('visible');
    btnToggle.classList.toggle('activo', estaVisible);
    btnToggle.setAttribute('aria-expanded', estaVisible ? 'true' : 'false');
  });
}

/**
 * Carga dinámica asíncrona de álbumes en móvil (Botón "Cargar más")
 */
function inicializarCargarMasDiscosAdmin() {
  const btnCargar = document.getElementById('btnCargarMasDiscos');
  const contenedorCards = document.getElementById('contenedorCardsDiscosMovil');
  const contadorProgreso = document.getElementById('contadorProgresoDiscos');
  const bloqueCargar = document.getElementById('bloqueCargarMasDiscos');

  if (!btnCargar || !contenedorCards) return;

  btnCargar.addEventListener('click', async () => {
    const paginaSiguiente = parseInt(btnCargar.dataset.paginaSiguiente, 10);
    const totalPaginas = parseInt(btnCargar.dataset.totalPaginas, 10);
    const categoria = btnCargar.dataset.categoria || '';
    const formato = btnCargar.dataset.formato || '';
    const baseUrl = btnCargar.dataset.url;

    if (btnCargar.classList.contains('cargando') || paginaSiguiente > totalPaginas) return;

    btnCargar.classList.add('cargando');
    const texto = btnCargar.querySelector('.texto-btn-cargar');
    if (texto) texto.textContent = 'Cargando álbumes...';

    try {
      const url = new URL(baseUrl, window.location.origin);
      url.searchParams.set('pagina', paginaSiguiente);
      if (categoria) url.searchParams.set('categoria_id', categoria);
      if (formato) url.searchParams.set('formato', formato);
      url.searchParams.set('ajax', '1');

      const respuesta = await fetch(url.toString(), {
        headers: {
          'X-Requested-With': 'XMLHttpRequest',
          'Accept': 'application/json'
        }
      });

      if (!respuesta.ok) throw new Error('Error al cargar más discos');

      const data = await respuesta.json();
      if (data.html) {
        const tempDiv = document.createElement('div');
        tempDiv.innerHTML = data.html;
        while (tempDiv.firstChild) {
          contenedorCards.appendChild(tempDiv.firstChild);
        }
      }

      const totalMostrados = Math.min(paginaSiguiente * 5, data.total);
      if (contadorProgreso) {
        contadorProgreso.textContent = `Mostrando ${totalMostrados} de ${data.total} discos`;
      }

      if (data.tiene_mas && paginaSiguiente < totalPaginas) {
        btnCargar.dataset.paginaSiguiente = (paginaSiguiente + 1).toString();
      } else {
        if (bloqueCargar) {
          bloqueCargar.style.display = 'none';
        }
      }
    } catch (err) {
      console.error('Error al cargar más álbumes:', err);
      if (texto) texto.textContent = 'Reintentar cargar más';
    } finally {
      btnCargar.classList.remove('cargando');
      const siguienteNum = parseInt(btnCargar.dataset.paginaSiguiente, 10);
      if (siguienteNum <= totalPaginas && texto) {
        texto.textContent = 'Cargar más álbumes';
      }
    }
  });
}

/**
 * Carga dinámica asíncrona de álbumes en móvil para el catálogo público (Botón "Cargar más")
 */
function inicializarCargarMasProductosCatalogo() {
  const btnCargar = document.getElementById('btnCargarMasCatalogo');
  const contenedorGrid = document.getElementById('gridProductosCatalogo');
  const contadorProgreso = document.getElementById('contadorProgresoCatalogo');
  const bloqueCargar = document.getElementById('bloqueCargarMasCatalogo');

  if (!btnCargar || !contenedorGrid) return;

  btnCargar.addEventListener('click', async () => {
    const paginaSiguiente = parseInt(btnCargar.dataset.paginaSiguiente, 10);
    const totalPaginas = parseInt(btnCargar.dataset.totalPaginas, 10);
    const categoria = btnCargar.dataset.categoria || '';
    const busqueda = btnCargar.dataset.q || '';
    const baseUrl = btnCargar.dataset.url;

    if (btnCargar.classList.contains('cargando') || paginaSiguiente > totalPaginas) return;

    btnCargar.classList.add('cargando');
    const texto = btnCargar.querySelector('.texto-btn-cargar');
    if (texto) texto.textContent = 'Cargando álbumes...';

    try {
      const url = new URL(baseUrl, window.location.origin);
      url.searchParams.set('pagina', paginaSiguiente);
      if (categoria && categoria !== 'todos') url.searchParams.set('categoria', categoria);
      if (busqueda) url.searchParams.set('q', busqueda);
      url.searchParams.set('ajax', '1');

      const respuesta = await fetch(url.toString(), {
        headers: {
          'X-Requested-With': 'XMLHttpRequest',
          'Accept': 'application/json'
        }
      });

      if (!respuesta.ok) throw new Error('Error al cargar más productos');

      const data = await respuesta.json();
      if (data.html) {
        const tempDiv = document.createElement('div');
        tempDiv.innerHTML = data.html;
        while (tempDiv.firstChild) {
          contenedorGrid.appendChild(tempDiv.firstChild);
        }
      }

      const porPagina = data.por_pagina || 6;
      const totalMostrados = Math.min(paginaSiguiente * porPagina, data.total);
      if (contadorProgreso) {
        contadorProgreso.textContent = `Mostrando ${totalMostrados} de ${data.total} álbumes`;
      }

      if (data.tiene_mas && paginaSiguiente < totalPaginas) {
        btnCargar.dataset.paginaSiguiente = (paginaSiguiente + 1).toString();
      } else {
        if (bloqueCargar) {
          bloqueCargar.style.display = 'none';
        }
      }
    } catch (err) {
      console.error('Error al cargar más productos del catálogo:', err);
      if (texto) texto.textContent = 'Reintentar cargar más';
    } finally {
      btnCargar.classList.remove('cargando');
      const siguienteNum = parseInt(btnCargar.dataset.paginaSiguiente, 10);
      if (siguienteNum <= totalPaginas && texto) {
        texto.textContent = 'Cargar más álbumes';
      }
    }
  });
}


