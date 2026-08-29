document.addEventListener('DOMContentLoaded', () => {
  const botonMenu = document.querySelector('.alternar-nav');
  const menuMobile = document.getElementById('navMovil');
  if (botonMenu && menuMobile) {
    botonMenu.addEventListener('click', () => menuMobile.classList.toggle('abierto'));
  }

  const params = new URLSearchParams(window.location.search);
  const categoria = params.get('categoria');
  const tarjetas = document.querySelectorAll('.tarjeta-producto');
  if (tarjetas.length && categoria) {
    tarjetas.forEach((card) => {
      card.style.display = card.getAttribute('data-categoria') === categoria ? '' : 'none';
    });
  }

  const categoriaActiva = categoria || 'todos';
  document.querySelectorAll('.botones-filtro [data-categoria]').forEach((link) => {
    link.classList.toggle('activo', link.getAttribute('data-categoria') === categoriaActiva);
  });

  const formulario = document.getElementById('contactForm');

  if (formulario) {
    formulario.addEventListener('submit', (e) => {
      e.preventDefault();

      if (validarFormulario()) {
        mostrarExito(formulario);
      } else {
        alert('Por favor, corrige los errores en el formulario.');
      }
    });
  }
});

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

