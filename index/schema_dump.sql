--
-- PostgreSQL database dump
--

-- Dumped from database version 16.4 (Ubuntu 16.4-0ubuntu0.24.04.2)
-- Dumped by pg_dump version 16.4 (Ubuntu 16.4-0ubuntu0.24.04.2)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
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
-- Name: bots; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.bots (
    bot_id integer NOT NULL,
    agent_name text NOT NULL,
    bot_type text NOT NULL,
    bot_ip inet NOT NULL
);


ALTER TABLE public.bots OWNER TO postgres;

--
-- Name: bots_bot_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.bots_bot_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.bots_bot_id_seq OWNER TO postgres;

--
-- Name: bots_bot_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.bots_bot_id_seq OWNED BY public.bots.bot_id;


--
-- Name: discovered_urls; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.discovered_urls (
    url_id integer NOT NULL,
    url text NOT NULL,
    processed timestamp without time zone NOT NULL
);


ALTER TABLE public.discovered_urls OWNER TO postgres;

--
-- Name: discovery; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.discovery (
    url_id integer NOT NULL,
    url text NOT NULL,
    referrer text,
    priority numeric(6,2) NOT NULL
);


ALTER TABLE public.discovery OWNER TO postgres;

--
-- Name: discovery_url_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.discovery_url_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.discovery_url_id_seq OWNER TO postgres;

--
-- Name: discovery_url_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.discovery_url_id_seq OWNED BY public.discovery.url_id;


--
-- Name: headers; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.headers (
    header_id integer NOT NULL,
    headers smallint NOT NULL,
    status smallint NOT NULL,
    x_frame text NOT NULL,
    content_type text NOT NULL,
    server text NOT NULL,
    cache_control text NOT NULL,
    cookies integer NOT NULL,
    set_cookie text NOT NULL,
    vary text NOT NULL,
    content_legth integer NOT NULL,
    connection text NOT NULL,
    content_lang text NOT NULL
);


ALTER TABLE public.headers OWNER TO postgres;

--
-- Name: headers_header_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.headers_header_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.headers_header_id_seq OWNER TO postgres;

--
-- Name: headers_header_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.headers_header_id_seq OWNED BY public.headers.header_id;


--
-- Name: links; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.links (
    link_id integer NOT NULL,
    id integer NOT NULL,
    link_dir boolean NOT NULL,
    s_url text NOT NULL,
    l_type boolean NOT NULL,
    anchor text NOT NULL,
    image boolean NOT NULL,
    alt_text text NOT NULL,
    nofollow boolean NOT NULL,
    first_seen timestamp without time zone NOT NULL,
    last_seen timestamp without time zone NOT NULL
);


ALTER TABLE public.links OWNER TO postgres;

--
-- Name: links_link_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.links_link_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.links_link_id_seq OWNER TO postgres;

--
-- Name: links_link_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.links_link_id_seq OWNED BY public.links.link_id;


--
-- Name: parameters; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.parameters (
    param_id integer NOT NULL,
    url text NOT NULL,
    p_string text NOT NULL,
    q_strings smallint NOT NULL,
    repeats boolean,
    more_3 boolean NOT NULL,
    sorted boolean,
    filtered boolean,
    pagination boolean,
    session_id boolean,
    tracking boolean
);


ALTER TABLE public.parameters OWNER TO postgres;

--
-- Name: parameters_param_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.parameters_param_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.parameters_param_id_seq OWNER TO postgres;

--
-- Name: parameters_param_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.parameters_param_id_seq OWNED BY public.parameters.param_id;


--
-- Name: performance; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.performance (
    performance_id integer NOT NULL,
    response_time numeric(7,2) NOT NULL,
    donload_time numeric(7,2) NOT NULL,
    dom_loaded numeric(7,2) NOT NULL,
    download_to_ready numeric(7,2) NOT NULL,
    dom_ready numeric(7,2) NOT NULL,
    fmp numeric(7,2) NOT NULL,
    tti numeric(7,2) NOT NULL,
    page_load numeric(7,2) NOT NULL,
    total_files integer NOT NULL,
    total_size numeric(10,2) NOT NULL,
    transfer_size numeric(9,2) NOT NULL,
    documents integer NOT NULL,
    document_size numeric(9,2) NOT NULL,
    doc_transfer_size numeric(9,2) NOT NULL,
    scripts integer NOT NULL,
    script_size numeric(9,2) NOT NULL,
    scripts_transfer_size numeric(9,2) NOT NULL,
    stylesheets integer NOT NULL,
    stylesheet_size numeric(9,2) NOT NULL,
    stylesheet_transfer_size numeric(9,2) NOT NULL,
    images integer NOT NULL,
    images_size numeric(9,2) NOT NULL,
    image_transfer_size numeric(9,2) NOT NULL,
    media integer NOT NULL,
    media_size numeric(9,2) NOT NULL,
    media_transfer_size numeric(9,2) NOT NULL,
    fonts integer NOT NULL,
    font_size numeric(9,2) NOT NULL,
    font_transfer_size numeric(9,2) NOT NULL,
    other_files integer NOT NULL,
    other_size numeric(9,2) NOT NULL,
    other_transfer_size numeric(9,2) NOT NULL,
    third_party integer NOT NULL,
    third_party_size numeric(9,2) NOT NULL,
    third_party_transfer_size numeric(9,2) NOT NULL,
    non_encoded smallint NOT NULL,
    scaled_images smallint NOT NULL,
    no_dimensions smallint NOT NULL,
    offscreen_not_deferred smallint NOT NULL,
    ttfb numeric(7,2) NOT NULL,
    un_minified_css smallint NOT NULL,
    un_minified_js smallint NOT NULL,
    uncompressed_text smallint NOT NULL,
    asset_cache_policy text NOT NULL,
    performance_score smallint NOT NULL,
    accessibility_score smallint NOT NULL,
    best_practice_score smallint NOT NULL,
    seo_score smallint NOT NULL,
    lcp_score numeric(7,2) NOT NULL,
    cls_score numeric(7,2) NOT NULL,
    tti_score numeric(7,2) NOT NULL,
    fcp_score numeric(7,2) NOT NULL,
    tbt numeric(7,2) NOT NULL,
    lcp_crux numeric(7,2) NOT NULL,
    cls_crux numeric(7,2) NOT NULL,
    fcp_crux numeric(7,2) NOT NULL,
    fid_crux numeric(7,2) NOT NULL,
    crux_error boolean NOT NULL,
    js_errors integer NOT NULL,
    viewport_missing smallint NOT NULL,
    viewport_multiple smallint NOT NULL,
    viewport_error smallint NOT NULL,
    viewport_width integer NOT NULL,
    is_responsive boolean NOT NULL
);


ALTER TABLE public.performance OWNER TO postgres;

--
-- Name: performance_performance_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.performance_performance_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.performance_performance_id_seq OWNER TO postgres;

--
-- Name: performance_performance_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.performance_performance_id_seq OWNED BY public.performance.performance_id;


--
-- Name: provider; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.provider (
    provider_id integer NOT NULL,
    p_name text NOT NULL,
    p_url text NOT NULL,
    onep_threep boolean NOT NULL,
    tier smallint NOT NULL
);


ALTER TABLE public.provider OWNER TO postgres;

--
-- Name: provider_provider_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.provider_provider_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.provider_provider_id_seq OWNER TO postgres;

--
-- Name: provider_provider_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.provider_provider_id_seq OWNED BY public.provider.provider_id;


--
-- Name: redirects; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.redirects (
    redirect_id integer NOT NULL,
    hops smallint NOT NULL,
    r_type text NOT NULL,
    r_url text NOT NULL,
    r_status smallint NOT NULL,
    r2_type text NOT NULL,
    r2_url text NOT NULL,
    r2_status smallint NOT NULL,
    r3_type text NOT NULL,
    r3_url text NOT NULL,
    r3_status smallint NOT NULL,
    r4_type text NOT NULL,
    r4_url text NOT NULL,
    r4_status smallint NOT NULL,
    r5_type text NOT NULL,
    r5_url text NOT NULL,
    r5_status smallint NOT NULL
);


ALTER TABLE public.redirects OWNER TO postgres;

--
-- Name: redirects_redirect_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.redirects_redirect_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.redirects_redirect_id_seq OWNER TO postgres;

--
-- Name: redirects_redirect_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.redirects_redirect_id_seq OWNED BY public.redirects.redirect_id;


--
-- Name: robots_txt; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.robots_txt (
    robots_id integer NOT NULL,
    url text NOT NULL,
    disallow text NOT NULL,
    bot_id integer NOT NULL,
    sitemaps text NOT NULL
);


ALTER TABLE public.robots_txt OWNER TO postgres;

--
-- Name: robots_txt_robots_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.robots_txt_robots_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.robots_txt_robots_id_seq OWNER TO postgres;

--
-- Name: robots_txt_robots_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.robots_txt_robots_id_seq OWNED BY public.robots_txt.robots_id;


--
-- Name: schema; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.schema (
    schema_id integer NOT NULL,
    entities smallint NOT NULL,
    failed_e smallint NOT NULL,
    passed_e smallint NOT NULL,
    errors smallint NOT NULL,
    articles boolean NOT NULL,
    bread_crumb boolean NOT NULL,
    event boolean NOT NULL,
    fact_check boolean NOT NULL,
    faq boolean NOT NULL,
    how_to boolean NOT NULL,
    image boolean NOT NULL,
    logo boolean NOT NULL,
    movie boolean NOT NULL,
    product boolean NOT NULL,
    recipe boolean NOT NULL,
    review boolean NOT NULL,
    sitelinks boolean NOT NULL,
    video boolean NOT NULL,
    f_articles boolean NOT NULL,
    f_bread_crumb boolean NOT NULL,
    f_event boolean NOT NULL,
    f_fact_check boolean NOT NULL,
    f_faq boolean NOT NULL,
    f_how_to boolean NOT NULL,
    f_image boolean NOT NULL,
    f_logo boolean NOT NULL,
    f_movie boolean NOT NULL,
    f_product boolean NOT NULL,
    f_recipe boolean NOT NULL,
    f_review boolean NOT NULL,
    f_sitelinks boolean NOT NULL,
    f_video boolean NOT NULL
);


ALTER TABLE public.schema OWNER TO postgres;

--
-- Name: schema_schema_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.schema_schema_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.schema_schema_id_seq OWNER TO postgres;

--
-- Name: schema_schema_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.schema_schema_id_seq OWNED BY public.schema.schema_id;


--
-- Name: search_console; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.search_console (
    console_id integer NOT NULL,
    clicks integer NOT NULL,
    impressions integer NOT NULL,
    avg_ctr numeric(5,2) NOT NULL,
    avg_position smallint NOT NULL,
    desktop_clicks integer NOT NULL,
    desktop_impressions integer NOT NULL,
    desktop_ctr numeric(5,2) NOT NULL,
    desktop_position smallint NOT NULL,
    mobile_clicks integer NOT NULL,
    mobile_impressions integer NOT NULL,
    mobile_ctr numeric(5,2) NOT NULL,
    mobile_position smallint NOT NULL,
    site_data_id integer NOT NULL,
    url_data_id integer NOT NULL
);


ALTER TABLE public.search_console OWNER TO postgres;

--
-- Name: search_console_console_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.search_console_console_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.search_console_console_id_seq OWNER TO postgres;

--
-- Name: search_console_console_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.search_console_console_id_seq OWNED BY public.search_console.console_id;


--
-- Name: site; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.site (
    site_id integer NOT NULL,
    site_name text NOT NULL,
    site_url text NOT NULL,
    seo_contact text NOT NULL,
    product_contact text NOT NULL,
    eng_contact text NOT NULL
);


ALTER TABLE public.site OWNER TO postgres;

--
-- Name: site_date; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.site_date (
    site_data_id integer NOT NULL,
    data_date date NOT NULL,
    site_url text NOT NULL,
    query text NOT NULL,
    is_anonymized_query boolean NOT NULL,
    country text NOT NULL,
    search_type text NOT NULL,
    device text NOT NULL,
    impressions integer NOT NULL,
    clicks integer NOT NULL,
    sum_top_position smallint NOT NULL
);


ALTER TABLE public.site_date OWNER TO postgres;

--
-- Name: site_date_site_data_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.site_date_site_data_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.site_date_site_data_id_seq OWNER TO postgres;

--
-- Name: site_date_site_data_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.site_date_site_data_id_seq OWNED BY public.site_date.site_data_id;


--
-- Name: site_site_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.site_site_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.site_site_id_seq OWNER TO postgres;

--
-- Name: site_site_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.site_site_id_seq OWNED BY public.site.site_id;


--
-- Name: url_data; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.url_data (
    url_data_id integer NOT NULL,
    data_date date NOT NULL,
    site_url text NOT NULL,
    url text NOT NULL,
    query text NOT NULL,
    is_anonymized_query boolean NOT NULL,
    is_anonymized_discover boolean NOT NULL,
    country text NOT NULL,
    search_type text NOT NULL,
    device text NOT NULL,
    is_amp_top_stories boolean NOT NULL,
    is_amp_blue_link boolean NOT NULL,
    is_job_listing boolean NOT NULL,
    is_job_details boolean NOT NULL,
    is_tpf_qa boolean NOT NULL,
    is_tpf_faq boolean NOT NULL,
    is_action boolean NOT NULL,
    is_search_appearance_android_app boolean NOT NULL,
    is_amp_story boolean NOT NULL,
    is_amp_image_result boolean NOT NULL,
    is_video boolean NOT NULL,
    is_review_snippet boolean NOT NULL,
    is_special_announcement boolean NOT NULL,
    is_recipe_feature boolean NOT NULL,
    is_recipe_rich_snippet boolean NOT NULL,
    is_subscribed_content boolean NOT NULL,
    is_practice_problems boolean NOT NULL,
    is_math_solvers boolean NOT NULL,
    is_translated_result boolean NOT NULL,
    is_edu_q_and_a boolean NOT NULL,
    is_product_snippets boolean NOT NULL,
    is_merchant_listings boolean NOT NULL,
    is_learning_videos boolean NOT NULL,
    impressions integer NOT NULL,
    clicks integer NOT NULL,
    sum_position smallint NOT NULL
);


ALTER TABLE public.url_data OWNER TO postgres;

--
-- Name: url_data_url_data_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.url_data_url_data_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.url_data_url_data_id_seq OWNER TO postgres;

--
-- Name: url_data_url_data_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.url_data_url_data_id_seq OWNED BY public.url_data.url_data_id;


--
-- Name: urls; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.urls (
    url_id integer NOT NULL,
    site_id integer NOT NULL,
    is_subdomain boolean NOT NULL,
    url text NOT NULL,
    hash bytea NOT NULL,
    slug text NOT NULL,
    referrer text NOT NULL,
    madhat_pr smallint NOT NULL,
    title text NOT NULL,
    title_len integer NOT NULL,
    description text NOT NULL,
    description_len integer NOT NULL,
    h1 smallint NOT NULL,
    h2 smallint NOT NULL,
    h3 smallint NOT NULL,
    h4 smallint NOT NULL,
    h5 smallint NOT NULL,
    h6 smallint NOT NULL,
    h1_text text NOT NULL,
    h1_len smallint NOT NULL,
    h1_words smallint NOT NULL,
    h1_2_text text NOT NULL,
    h1_2_len smallint NOT NULL,
    h1_2_words smallint NOT NULL,
    provider_id integer NOT NULL,
    publish timestamp without time zone NOT NULL,
    modified timestamp without time zone NOT NULL,
    blocked boolean NOT NULL,
    robots_id integer NOT NULL,
    in_sitemaps boolean NOT NULL,
    multiple_sitemaps boolean NOT NULL,
    sitemap_url text NOT NULL,
    m_robots text NOT NULL,
    c_status boolean NOT NULL,
    canonical text NOT NULL,
    r_url boolean NOT NULL,
    redirect_id integer NOT NULL,
    amp text NOT NULL,
    href boolean NOT NULL,
    viewport boolean NOT NULL,
    "x-rdrctid" text NOT NULL,
    params boolean NOT NULL,
    param_id integer NOT NULL,
    depth smallint NOT NULL,
    header_id integer NOT NULL,
    performance_id integer NOT NULL,
    schema boolean NOT NULL,
    schema_id integer NOT NULL,
    nocache boolean NOT NULL,
    noarchive boolean NOT NULL,
    nosnippet boolean NOT NULL,
    max_snippet boolean NOT NULL,
    max_image boolean NOT NULL,
    max_video boolean NOT NULL,
    words integer NOT NULL,
    sentences integer NOT NULL,
    avg_sentence integer NOT NULL,
    flesch smallint NOT NULL,
    read text NOT NULL,
    grade text NOT NULL,
    inlinks integer NOT NULL,
    u_inlinks integer NOT NULL,
    outlinks integer NOT NULL,
    u_outlinks integer NOT NULL,
    follow_nofollow boolean NOT NULL,
    in_nofollow integer NOT NULL,
    o_nofollow integer NOT NULL,
    js_links integer NOT NULL,
    content_links integer NOT NULL,
    nav_links integer NOT NULL,
    image_links integer NOT NULL,
    other_links integer NOT NULL,
    console_id integer NOT NULL,
    "timestamp" timestamp without time zone NOT NULL
);


ALTER TABLE public.urls OWNER TO postgres;

--
-- Name: urls_url_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.urls_url_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.urls_url_id_seq OWNER TO postgres;

--
-- Name: urls_url_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.urls_url_id_seq OWNED BY public.urls.url_id;


--
-- Name: bots bot_id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.bots ALTER COLUMN bot_id SET DEFAULT nextval('public.bots_bot_id_seq'::regclass);


--
-- Name: discovery url_id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.discovery ALTER COLUMN url_id SET DEFAULT nextval('public.discovery_url_id_seq'::regclass);


--
-- Name: headers header_id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.headers ALTER COLUMN header_id SET DEFAULT nextval('public.headers_header_id_seq'::regclass);


--
-- Name: links link_id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.links ALTER COLUMN link_id SET DEFAULT nextval('public.links_link_id_seq'::regclass);


--
-- Name: parameters param_id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.parameters ALTER COLUMN param_id SET DEFAULT nextval('public.parameters_param_id_seq'::regclass);


--
-- Name: performance performance_id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.performance ALTER COLUMN performance_id SET DEFAULT nextval('public.performance_performance_id_seq'::regclass);


--
-- Name: provider provider_id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.provider ALTER COLUMN provider_id SET DEFAULT nextval('public.provider_provider_id_seq'::regclass);


--
-- Name: redirects redirect_id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.redirects ALTER COLUMN redirect_id SET DEFAULT nextval('public.redirects_redirect_id_seq'::regclass);


--
-- Name: robots_txt robots_id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.robots_txt ALTER COLUMN robots_id SET DEFAULT nextval('public.robots_txt_robots_id_seq'::regclass);


--
-- Name: schema schema_id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.schema ALTER COLUMN schema_id SET DEFAULT nextval('public.schema_schema_id_seq'::regclass);


--
-- Name: search_console console_id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.search_console ALTER COLUMN console_id SET DEFAULT nextval('public.search_console_console_id_seq'::regclass);


--
-- Name: site site_id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.site ALTER COLUMN site_id SET DEFAULT nextval('public.site_site_id_seq'::regclass);


--
-- Name: site_date site_data_id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.site_date ALTER COLUMN site_data_id SET DEFAULT nextval('public.site_date_site_data_id_seq'::regclass);


--
-- Name: url_data url_data_id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.url_data ALTER COLUMN url_data_id SET DEFAULT nextval('public.url_data_url_data_id_seq'::regclass);


--
-- Name: urls url_id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.urls ALTER COLUMN url_id SET DEFAULT nextval('public.urls_url_id_seq'::regclass);


--
-- Name: bots pk_bots; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.bots
    ADD CONSTRAINT pk_bots PRIMARY KEY (bot_id);


--
-- Name: discovered_urls pk_discovered_urls; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.discovered_urls
    ADD CONSTRAINT pk_discovered_urls PRIMARY KEY (url_id);


--
-- Name: discovery pk_discovery; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.discovery
    ADD CONSTRAINT pk_discovery PRIMARY KEY (url_id);


--
-- Name: headers pk_headers; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.headers
    ADD CONSTRAINT pk_headers PRIMARY KEY (header_id);


--
-- Name: links pk_links; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.links
    ADD CONSTRAINT pk_links PRIMARY KEY (link_id);


--
-- Name: parameters pk_parameters; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.parameters
    ADD CONSTRAINT pk_parameters PRIMARY KEY (param_id);


--
-- Name: performance pk_performance; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.performance
    ADD CONSTRAINT pk_performance PRIMARY KEY (performance_id);


--
-- Name: provider pk_provider; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.provider
    ADD CONSTRAINT pk_provider PRIMARY KEY (provider_id);


--
-- Name: redirects pk_redirects; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.redirects
    ADD CONSTRAINT pk_redirects PRIMARY KEY (redirect_id);


--
-- Name: robots_txt pk_robots_txt; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.robots_txt
    ADD CONSTRAINT pk_robots_txt PRIMARY KEY (robots_id);


--
-- Name: schema pk_schema; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.schema
    ADD CONSTRAINT pk_schema PRIMARY KEY (schema_id);


--
-- Name: search_console pk_search_console; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.search_console
    ADD CONSTRAINT pk_search_console PRIMARY KEY (console_id);


--
-- Name: site pk_site; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.site
    ADD CONSTRAINT pk_site PRIMARY KEY (site_id);


--
-- Name: site_date pk_site_date; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.site_date
    ADD CONSTRAINT pk_site_date PRIMARY KEY (site_data_id);


--
-- Name: url_data pk_url_data; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.url_data
    ADD CONSTRAINT pk_url_data PRIMARY KEY (url_data_id);


--
-- Name: urls pk_urls; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.urls
    ADD CONSTRAINT pk_urls PRIMARY KEY (url_id);


--
-- Name: urls uc_urls_hash; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.urls
    ADD CONSTRAINT uc_urls_hash UNIQUE (hash);


--
-- Name: parameters unique_p_string; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.parameters
    ADD CONSTRAINT unique_p_string UNIQUE (p_string);


--
-- Name: idx_priority; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_priority ON public.discovery USING btree (priority);


--
-- Name: idx_url; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_url ON public.parameters USING btree (url);


--
-- Name: discovered_urls fk_discovered_urls_url_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.discovered_urls
    ADD CONSTRAINT fk_discovered_urls_url_id FOREIGN KEY (url_id) REFERENCES public.discovery(url_id);


--
-- Name: robots_txt fk_robots_txt_bot_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.robots_txt
    ADD CONSTRAINT fk_robots_txt_bot_id FOREIGN KEY (bot_id) REFERENCES public.bots(bot_id);


--
-- Name: search_console fk_search_console_site_data_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.search_console
    ADD CONSTRAINT fk_search_console_site_data_id FOREIGN KEY (site_data_id) REFERENCES public.site_date(site_data_id);


--
-- Name: search_console fk_search_console_url_data_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.search_console
    ADD CONSTRAINT fk_search_console_url_data_id FOREIGN KEY (url_data_id) REFERENCES public.url_data(url_data_id);


--
-- Name: urls fk_urls_console_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.urls
    ADD CONSTRAINT fk_urls_console_id FOREIGN KEY (console_id) REFERENCES public.search_console(console_id);


--
-- Name: urls fk_urls_header_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.urls
    ADD CONSTRAINT fk_urls_header_id FOREIGN KEY (header_id) REFERENCES public.headers(header_id);


--
-- Name: urls fk_urls_param_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.urls
    ADD CONSTRAINT fk_urls_param_id FOREIGN KEY (param_id) REFERENCES public.parameters(param_id);


--
-- Name: urls fk_urls_performance_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.urls
    ADD CONSTRAINT fk_urls_performance_id FOREIGN KEY (performance_id) REFERENCES public.performance(performance_id);


--
-- Name: urls fk_urls_provider_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.urls
    ADD CONSTRAINT fk_urls_provider_id FOREIGN KEY (provider_id) REFERENCES public.provider(provider_id);


--
-- Name: urls fk_urls_redirect_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.urls
    ADD CONSTRAINT fk_urls_redirect_id FOREIGN KEY (redirect_id) REFERENCES public.redirects(redirect_id);


--
-- Name: urls fk_urls_robots_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.urls
    ADD CONSTRAINT fk_urls_robots_id FOREIGN KEY (robots_id) REFERENCES public.robots_txt(robots_id);


--
-- Name: urls fk_urls_schema_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.urls
    ADD CONSTRAINT fk_urls_schema_id FOREIGN KEY (schema_id) REFERENCES public.schema(schema_id);


--
-- Name: urls fk_urls_site_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.urls
    ADD CONSTRAINT fk_urls_site_id FOREIGN KEY (site_id) REFERENCES public.site(site_id);


--
-- Name: urls fk_urls_url_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.urls
    ADD CONSTRAINT fk_urls_url_id FOREIGN KEY (url_id) REFERENCES public.discovery(url_id);


--
-- PostgreSQL database dump complete
--

