--
-- PostgreSQL database dump
--

\restrict K0qWICH4IxRZchDI6GDWDdlIxXpoE7ilPj9fDOWnuV9d3uKml5tAwLaKwfxPE4Z

-- Dumped from database version 18.1
-- Dumped by pg_dump version 18.1

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: categorias; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.categorias (
    id integer NOT NULL,
    nombre character varying(80) NOT NULL,
    slug character varying(90) NOT NULL,
    descripcion text,
    imagen character varying(255),
    activo boolean DEFAULT true NOT NULL,
    fecha_creacion timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    fecha_actualizacion timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


--
-- Name: categorias_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.categorias_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: categorias_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.categorias_id_seq OWNED BY public.categorias.id;


--
-- Name: detalles_pedido; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.detalles_pedido (
    id integer NOT NULL,
    pedido_id integer NOT NULL,
    disco_id integer NOT NULL,
    album character varying(150) NOT NULL,
    artista character varying(120) NOT NULL,
    formato character varying(10) NOT NULL,
    precio_unitario numeric(10,2) NOT NULL,
    cantidad integer NOT NULL,
    CONSTRAINT ck_detalles_cantidad CHECK ((cantidad > 0)),
    CONSTRAINT ck_detalles_precio_unitario CHECK ((precio_unitario >= (0)::numeric))
);


--
-- Name: detalles_pedido_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.detalles_pedido_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: detalles_pedido_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.detalles_pedido_id_seq OWNED BY public.detalles_pedido.id;


--
-- Name: discos; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.discos (
    id integer NOT NULL,
    categoria_id integer NOT NULL,
    codigo character varying(30) NOT NULL,
    album character varying(150) NOT NULL,
    artista character varying(120) NOT NULL,
    descripcion text NOT NULL,
    precio_base numeric(10,2) NOT NULL,
    stock integer DEFAULT 0 NOT NULL,
    formato character varying(10) NOT NULL,
    peso_kg numeric(6,3) NOT NULL,
    costo_envio_por_kg numeric(10,2) DEFAULT '0'::numeric NOT NULL,
    costo_embalaje numeric(10,2) DEFAULT '0'::numeric NOT NULL,
    imagen character varying(255),
    activo boolean DEFAULT true NOT NULL,
    fecha_creacion timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    fecha_actualizacion timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT ck_discos_costo_embalaje CHECK ((costo_embalaje >= (0)::numeric)),
    CONSTRAINT ck_discos_costo_envio CHECK ((costo_envio_por_kg >= (0)::numeric)),
    CONSTRAINT ck_discos_formato CHECK (((formato)::text = ANY ((ARRAY['CD'::character varying, 'VINILO'::character varying])::text[]))),
    CONSTRAINT ck_discos_peso CHECK ((peso_kg > (0)::numeric)),
    CONSTRAINT ck_discos_precio CHECK ((precio_base >= (0)::numeric)),
    CONSTRAINT ck_discos_stock CHECK ((stock >= 0))
);


--
-- Name: discos_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.discos_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: discos_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.discos_id_seq OWNED BY public.discos.id;


--
-- Name: facturas; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.facturas (
    id integer NOT NULL,
    pedido_id integer NOT NULL,
    numero character varying(30) NOT NULL,
    tipo character varying(30) NOT NULL,
    fecha_emision timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    ruta_pdf character varying(255) NOT NULL,
    CONSTRAINT ck_facturas_tipo CHECK (((tipo)::text = ANY ((ARRAY['COMPROBANTE_PENDIENTE'::character varying, 'FACTURA_FINAL'::character varying])::text[])))
);


--
-- Name: facturas_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.facturas_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: facturas_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.facturas_id_seq OWNED BY public.facturas.id;


--
-- Name: metodos_pago; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.metodos_pago (
    id integer NOT NULL,
    usuario_id integer NOT NULL,
    token character varying(120) NOT NULL,
    marca character varying(30) NOT NULL,
    ultimos4 character varying(4) NOT NULL,
    titular character varying(120) NOT NULL,
    mes_vencimiento integer NOT NULL,
    anio_vencimiento integer NOT NULL,
    predeterminado boolean DEFAULT false NOT NULL,
    activo boolean DEFAULT true NOT NULL,
    fecha_verificacion timestamp with time zone NOT NULL,
    CONSTRAINT ck_metodos_pago_anio_vencimiento CHECK ((anio_vencimiento >= 2026)),
    CONSTRAINT ck_metodos_pago_mes_vencimiento CHECK (((mes_vencimiento >= 1) AND (mes_vencimiento <= 12))),
    CONSTRAINT ck_metodos_pago_ultimos4 CHECK (((ultimos4)::text ~ '^[0-9]{4}$'::text))
);


--
-- Name: metodos_pago_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.metodos_pago_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: metodos_pago_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.metodos_pago_id_seq OWNED BY public.metodos_pago.id;


--
-- Name: pedidos; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.pedidos (
    id integer NOT NULL,
    numero character varying(24) NOT NULL,
    cliente_id integer NOT NULL,
    metodo_pago_id integer NOT NULL,
    estado character varying(20) DEFAULT 'PENDIENTE'::character varying NOT NULL,
    total numeric(10,2) NOT NULL,
    fecha_creacion timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    fecha_revision timestamp with time zone,
    administrador_revisor_id integer,
    motivo_rechazo character varying(255),
    CONSTRAINT ck_pedidos_estado CHECK (((estado)::text = ANY ((ARRAY['PENDIENTE'::character varying, 'APROBADO'::character varying, 'RECHAZADO'::character varying])::text[]))),
    CONSTRAINT ck_pedidos_rechazo_con_motivo CHECK ((((estado)::text <> 'RECHAZADO'::text) OR (motivo_rechazo IS NOT NULL))),
    CONSTRAINT ck_pedidos_total CHECK ((total >= (0)::numeric))
);


--
-- Name: pedidos_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.pedidos_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: pedidos_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.pedidos_id_seq OWNED BY public.pedidos.id;


--
-- Name: transacciones_pago; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.transacciones_pago (
    id integer NOT NULL,
    pedido_id integer NOT NULL,
    metodo_pago_id integer NOT NULL,
    monto numeric(10,2) NOT NULL,
    estado character varying(20) DEFAULT 'PENDIENTE'::character varying NOT NULL,
    referencia character varying(80) NOT NULL,
    fecha_procesamiento timestamp with time zone,
    CONSTRAINT ck_transacciones_estado CHECK (((estado)::text = ANY ((ARRAY['PENDIENTE'::character varying, 'APROBADA'::character varying, 'RECHAZADA'::character varying])::text[]))),
    CONSTRAINT ck_transacciones_monto CHECK ((monto >= (0)::numeric))
);


--
-- Name: transacciones_pago_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.transacciones_pago_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: transacciones_pago_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.transacciones_pago_id_seq OWNED BY public.transacciones_pago.id;


--
-- Name: usuarios; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.usuarios (
    id integer NOT NULL,
    nombre character varying(100) NOT NULL,
    email character varying(120) NOT NULL,
    password_hash character varying(255) NOT NULL,
    rol character varying(20) DEFAULT 'cliente'::character varying NOT NULL,
    telefono character varying(20),
    direccion character varying(200),
    ciudad character varying(100),
    activo boolean DEFAULT true NOT NULL,
    fecha_registro timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT ck_usuarios_email_formato CHECK (((email)::text ~ '^[^@ ]+@[^@ ]+\.[^@ ]+$'::text)),
    CONSTRAINT ck_usuarios_email_normalizado CHECK (((email)::text = lower(btrim((email)::text)))),
    CONSTRAINT ck_usuarios_nombre_valido CHECK (((char_length(btrim((nombre)::text)) >= 2) AND (char_length(btrim((nombre)::text)) <= 100))),
    CONSTRAINT ck_usuarios_rol CHECK (((rol)::text = ANY ((ARRAY['cliente'::character varying, 'administrador'::character varying])::text[])))
);


--
-- Name: usuarios_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.usuarios_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: usuarios_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.usuarios_id_seq OWNED BY public.usuarios.id;


--
-- Name: verificaciones_tarjeta; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.verificaciones_tarjeta (
    id integer NOT NULL,
    usuario_id integer NOT NULL,
    token_verificacion character varying(64) NOT NULL,
    pin_hash character varying(255) NOT NULL,
    token_tarjeta character varying(120) NOT NULL,
    marca character varying(30) NOT NULL,
    ultimos4 character varying(4) NOT NULL,
    titular character varying(120) NOT NULL,
    mes_vencimiento integer NOT NULL,
    anio_vencimiento integer NOT NULL,
    fecha_creacion timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    fecha_expiracion timestamp with time zone NOT NULL,
    intentos integer DEFAULT 0 NOT NULL,
    verificada boolean DEFAULT false NOT NULL,
    CONSTRAINT ck_verificaciones_intentos CHECK (((intentos >= 0) AND (intentos <= 5))),
    CONSTRAINT ck_verificaciones_mes_vencimiento CHECK (((mes_vencimiento >= 1) AND (mes_vencimiento <= 12))),
    CONSTRAINT ck_verificaciones_ultimos4 CHECK (((ultimos4)::text ~ '^[0-9]{4}$'::text))
);


--
-- Name: verificaciones_tarjeta_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.verificaciones_tarjeta_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: verificaciones_tarjeta_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.verificaciones_tarjeta_id_seq OWNED BY public.verificaciones_tarjeta.id;


--
-- Name: categorias id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.categorias ALTER COLUMN id SET DEFAULT nextval('public.categorias_id_seq'::regclass);


--
-- Name: detalles_pedido id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.detalles_pedido ALTER COLUMN id SET DEFAULT nextval('public.detalles_pedido_id_seq'::regclass);


--
-- Name: discos id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.discos ALTER COLUMN id SET DEFAULT nextval('public.discos_id_seq'::regclass);


--
-- Name: facturas id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.facturas ALTER COLUMN id SET DEFAULT nextval('public.facturas_id_seq'::regclass);


--
-- Name: metodos_pago id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.metodos_pago ALTER COLUMN id SET DEFAULT nextval('public.metodos_pago_id_seq'::regclass);


--
-- Name: pedidos id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.pedidos ALTER COLUMN id SET DEFAULT nextval('public.pedidos_id_seq'::regclass);


--
-- Name: transacciones_pago id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.transacciones_pago ALTER COLUMN id SET DEFAULT nextval('public.transacciones_pago_id_seq'::regclass);


--
-- Name: usuarios id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.usuarios ALTER COLUMN id SET DEFAULT nextval('public.usuarios_id_seq'::regclass);


--
-- Name: verificaciones_tarjeta id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.verificaciones_tarjeta ALTER COLUMN id SET DEFAULT nextval('public.verificaciones_tarjeta_id_seq'::regclass);


--
-- Name: categorias categorias_nombre_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.categorias
    ADD CONSTRAINT categorias_nombre_key UNIQUE (nombre);


--
-- Name: categorias categorias_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.categorias
    ADD CONSTRAINT categorias_pkey PRIMARY KEY (id);


--
-- Name: detalles_pedido detalles_pedido_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.detalles_pedido
    ADD CONSTRAINT detalles_pedido_pkey PRIMARY KEY (id);


--
-- Name: discos discos_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.discos
    ADD CONSTRAINT discos_pkey PRIMARY KEY (id);


--
-- Name: facturas facturas_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.facturas
    ADD CONSTRAINT facturas_pkey PRIMARY KEY (id);


--
-- Name: metodos_pago metodos_pago_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.metodos_pago
    ADD CONSTRAINT metodos_pago_pkey PRIMARY KEY (id);


--
-- Name: metodos_pago metodos_pago_token_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.metodos_pago
    ADD CONSTRAINT metodos_pago_token_key UNIQUE (token);


--
-- Name: pedidos pedidos_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.pedidos
    ADD CONSTRAINT pedidos_pkey PRIMARY KEY (id);


--
-- Name: transacciones_pago transacciones_pago_pedido_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.transacciones_pago
    ADD CONSTRAINT transacciones_pago_pedido_id_key UNIQUE (pedido_id);


--
-- Name: transacciones_pago transacciones_pago_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.transacciones_pago
    ADD CONSTRAINT transacciones_pago_pkey PRIMARY KEY (id);


--
-- Name: transacciones_pago transacciones_pago_referencia_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.transacciones_pago
    ADD CONSTRAINT transacciones_pago_referencia_key UNIQUE (referencia);


--
-- Name: detalles_pedido uq_detalles_pedido_disco; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.detalles_pedido
    ADD CONSTRAINT uq_detalles_pedido_disco UNIQUE (pedido_id, disco_id);


--
-- Name: facturas uq_facturas_pedido_tipo; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.facturas
    ADD CONSTRAINT uq_facturas_pedido_tipo UNIQUE (pedido_id, tipo);


--
-- Name: usuarios usuarios_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.usuarios
    ADD CONSTRAINT usuarios_pkey PRIMARY KEY (id);


--
-- Name: verificaciones_tarjeta verificaciones_tarjeta_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.verificaciones_tarjeta
    ADD CONSTRAINT verificaciones_tarjeta_pkey PRIMARY KEY (id);


--
-- Name: verificaciones_tarjeta verificaciones_tarjeta_token_verificacion_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.verificaciones_tarjeta
    ADD CONSTRAINT verificaciones_tarjeta_token_verificacion_key UNIQUE (token_verificacion);


--
-- Name: ix_categorias_slug; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_categorias_slug ON public.categorias USING btree (slug);


--
-- Name: ix_detalles_pedido_disco_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_detalles_pedido_disco_id ON public.detalles_pedido USING btree (disco_id);


--
-- Name: ix_detalles_pedido_pedido_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_detalles_pedido_pedido_id ON public.detalles_pedido USING btree (pedido_id);


--
-- Name: ix_discos_artista; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_discos_artista ON public.discos USING btree (artista);


--
-- Name: ix_discos_categoria_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_discos_categoria_id ON public.discos USING btree (categoria_id);


--
-- Name: ix_discos_codigo; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_discos_codigo ON public.discos USING btree (codigo);


--
-- Name: ix_discos_formato; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_discos_formato ON public.discos USING btree (formato);


--
-- Name: ix_facturas_numero; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_facturas_numero ON public.facturas USING btree (numero);


--
-- Name: ix_facturas_pedido_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_facturas_pedido_id ON public.facturas USING btree (pedido_id);


--
-- Name: ix_metodos_pago_usuario_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_metodos_pago_usuario_id ON public.metodos_pago USING btree (usuario_id);


--
-- Name: ix_pedidos_administrador_revisor_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_pedidos_administrador_revisor_id ON public.pedidos USING btree (administrador_revisor_id);


--
-- Name: ix_pedidos_cliente_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_pedidos_cliente_id ON public.pedidos USING btree (cliente_id);


--
-- Name: ix_pedidos_numero; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_pedidos_numero ON public.pedidos USING btree (numero);


--
-- Name: ix_usuarios_email; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_usuarios_email ON public.usuarios USING btree (email);


--
-- Name: ix_verificaciones_tarjeta_usuario_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_verificaciones_tarjeta_usuario_id ON public.verificaciones_tarjeta USING btree (usuario_id);


--
-- Name: detalles_pedido detalles_pedido_disco_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.detalles_pedido
    ADD CONSTRAINT detalles_pedido_disco_id_fkey FOREIGN KEY (disco_id) REFERENCES public.discos(id) ON DELETE RESTRICT;


--
-- Name: detalles_pedido detalles_pedido_pedido_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.detalles_pedido
    ADD CONSTRAINT detalles_pedido_pedido_id_fkey FOREIGN KEY (pedido_id) REFERENCES public.pedidos(id) ON DELETE CASCADE;


--
-- Name: discos discos_categoria_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.discos
    ADD CONSTRAINT discos_categoria_id_fkey FOREIGN KEY (categoria_id) REFERENCES public.categorias(id) ON DELETE RESTRICT;


--
-- Name: facturas facturas_pedido_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.facturas
    ADD CONSTRAINT facturas_pedido_id_fkey FOREIGN KEY (pedido_id) REFERENCES public.pedidos(id) ON DELETE CASCADE;


--
-- Name: metodos_pago metodos_pago_usuario_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.metodos_pago
    ADD CONSTRAINT metodos_pago_usuario_id_fkey FOREIGN KEY (usuario_id) REFERENCES public.usuarios(id) ON DELETE CASCADE;


--
-- Name: pedidos pedidos_administrador_revisor_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.pedidos
    ADD CONSTRAINT pedidos_administrador_revisor_id_fkey FOREIGN KEY (administrador_revisor_id) REFERENCES public.usuarios(id) ON DELETE SET NULL;


--
-- Name: pedidos pedidos_cliente_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.pedidos
    ADD CONSTRAINT pedidos_cliente_id_fkey FOREIGN KEY (cliente_id) REFERENCES public.usuarios(id) ON DELETE RESTRICT;


--
-- Name: pedidos pedidos_metodo_pago_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.pedidos
    ADD CONSTRAINT pedidos_metodo_pago_id_fkey FOREIGN KEY (metodo_pago_id) REFERENCES public.metodos_pago(id) ON DELETE RESTRICT;


--
-- Name: transacciones_pago transacciones_pago_metodo_pago_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.transacciones_pago
    ADD CONSTRAINT transacciones_pago_metodo_pago_id_fkey FOREIGN KEY (metodo_pago_id) REFERENCES public.metodos_pago(id) ON DELETE RESTRICT;


--
-- Name: transacciones_pago transacciones_pago_pedido_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.transacciones_pago
    ADD CONSTRAINT transacciones_pago_pedido_id_fkey FOREIGN KEY (pedido_id) REFERENCES public.pedidos(id) ON DELETE CASCADE;


--
-- Name: verificaciones_tarjeta verificaciones_tarjeta_usuario_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.verificaciones_tarjeta
    ADD CONSTRAINT verificaciones_tarjeta_usuario_id_fkey FOREIGN KEY (usuario_id) REFERENCES public.usuarios(id) ON DELETE CASCADE;


--
-- PostgreSQL database dump complete
--

\unrestrict K0qWICH4IxRZchDI6GDWDdlIxXpoE7ilPj9fDOWnuV9d3uKml5tAwLaKwfxPE4Z
