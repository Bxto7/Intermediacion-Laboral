"""
Demo seed — DRTPE-Junín · Presentación al Ministerio
======================================================
Genera datos realistas basados en perfiles de empleosperu.gob.pe para la región Junín.

Uso:
  docker exec intermediacion_api python scripts/seed_demo.py

  O con venv activo:
  python scripts/seed_demo.py
"""
import asyncio
import os
import sys
import uuid

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.core.security import encrypt_field, hash_password
from app.models.service_listing import ServiceListing
from app.models.user import User
from app.models.worker import Worker

# ── DATOS REALISTAS BASADOS EN EMPLEOS PERÚ — REGIÓN JUNÍN ─────────────────
# Fuente: empleosperu.gob.pe y bolsa de trabajo DRTPE-Junín (categorías oficio)

OFICIO_WORKERS = [
    # ── ELECTRICIDAD ──────────────────────────────────────────────────────────
    {
        "full_name": "Carlos Alberto Huamán Quispe",
        "username": "carlos_electricista_hyo",
        "trade_category": "Electricidad",
        "district": "Huancayo",
        "years_experience": 8,
        "avg_rating": Decimal("4.80"),
        "bio": "Técnico electricista con 8 años de experiencia en instalaciones residenciales e industriales en la región Junín. Certificado SENATI. Trabajo garantizado.",
        "job_title": "Técnico Electricista",
        "email": "carlos.huaman@demo.pe",
        "listings": [
            {
                "trade_category": "Electricidad",
                "title": "Instalación eléctrica residencial completa",
                "description": "Realizo instalaciones eléctricas completas para casas y departamentos. Incluye tablero de distribución, circuitos monofásicos, tomacorrientes, puntos de luz y puesta a tierra. Materiales de primera calidad con garantía de 1 año.",
                "enriched_keywords": ["instalación eléctrica", "tablero eléctrico", "tomacorrientes", "puesta a tierra", "circuito monofásico", "luminarias"],
                "districts": ["Huancayo", "El Tambo"],
                "price_reference": Decimal("45.00"),
                "price_unit": "hora",
                "availability": "inmediata",
                "views_count": 47,
            },
            {
                "trade_category": "Electricidad",
                "title": "Cambio y reparación de tablero eléctrico",
                "description": "Cambio de tableros eléctricos dañados o antiguos. Instalación de llaves termomagnéticas, protectores de sobretensión y diferencial. Cumple normas del Código Nacional de Electricidad.",
                "enriched_keywords": ["tablero eléctrico", "llave termomagnética", "diferencial", "sobretensión", "norma eléctrica"],
                "districts": ["Huancayo", "El Tambo", "Chilca"],
                "price_reference": Decimal("200.00"),
                "price_unit": "proyecto",
                "availability": "inmediata",
                "views_count": 31,
            },
        ],
    },
    {
        "full_name": "Ricardo Flores Palomino",
        "username": "ricardo_electro_tambo",
        "trade_category": "Electricidad",
        "district": "El Tambo",
        "years_experience": 12,
        "avg_rating": Decimal("4.95"),
        "bio": "Electricista con 12 años de experiencia. Egresado SENATI Huancayo. Especializado en instalaciones trifásicas para industria y comercio. Atención de emergencias.",
        "job_title": "Electricista Industrial y Residencial",
        "email": "ricardo.flores@demo.pe",
        "listings": [
            {
                "trade_category": "Electricidad",
                "title": "Instalación eléctrica para locales comerciales",
                "description": "Diseño e instalación de sistemas eléctricos para tiendas, restaurantes y oficinas. Incluye planos eléctricos, instalación trifásica, pozos a tierra y certificado de conformidad.",
                "enriched_keywords": ["instalación comercial", "sistema trifásico", "plano eléctrico", "pozo a tierra", "certificado"],
                "districts": ["El Tambo", "Huancayo"],
                "price_reference": Decimal("380.00"),
                "price_unit": "proyecto",
                "availability": "semana",
                "views_count": 28,
            },
            {
                "trade_category": "Electricidad",
                "title": "Instalación de tomacorrientes y puntos de luz",
                "description": "Instalación de tomacorrientes dobles, triples y con toma a tierra. Puntos de luz para sala, cocina, dormitorios y exteriores. Trabajo limpio sin romper paredes innecesariamente.",
                "enriched_keywords": ["tomacorriente", "punto de luz", "instalación domiciliaria", "cableado"],
                "districts": ["El Tambo", "Huancayo", "Chilca"],
                "price_reference": Decimal("40.00"),
                "price_unit": "hora",
                "availability": "inmediata",
                "views_count": 55,
            },
        ],
    },

    # ── GASFITERÍA ────────────────────────────────────────────────────────────
    {
        "full_name": "Juan Pablo Quispe Ore",
        "username": "juan_gasfitero_hyo",
        "trade_category": "Gasfitería",
        "district": "Huancayo",
        "years_experience": 10,
        "avg_rating": Decimal("4.70"),
        "bio": "Gasfitero con más de 10 años instalando y reparando sistemas sanitarios en Huancayo. Especializado en agua fría, agua caliente y desagüe. Servicio de emergencia.",
        "job_title": "Gasfitero Certificado",
        "email": "juan.quispe@demo.pe",
        "listings": [
            {
                "trade_category": "Gasfitería",
                "title": "Instalación de baño completo desde cero",
                "description": "Instalo baños completos: tubería de agua fría y caliente, desagüe, inodoro, lavatorio, ducha y accesorios. Materiales garantizados. Trabajo prolijo con sellado anti-humedad.",
                "enriched_keywords": ["instalación baño", "tubería sanitaria", "inodoro", "lavatorio", "ducha", "desagüe", "agua caliente"],
                "districts": ["Huancayo", "El Tambo"],
                "price_reference": Decimal("650.00"),
                "price_unit": "proyecto",
                "availability": "semana",
                "views_count": 39,
            },
            {
                "trade_category": "Gasfitería",
                "title": "Reparación de tuberías y fugas de agua urgente",
                "description": "Detección y reparación de fugas en tuberías empotradas y externas. Cambio de tuberías PVC y CPVC. Atención de emergencias los 7 días. Presupuesto sin costo.",
                "enriched_keywords": ["reparación de fuga", "tubería PVC", "emergencia fontanería", "cambio de tuberías", "plomería"],
                "districts": ["Huancayo", "El Tambo", "Chilca"],
                "price_reference": Decimal("50.00"),
                "price_unit": "hora",
                "availability": "inmediata",
                "views_count": 62,
            },
        ],
    },
    {
        "full_name": "Miguel Ángel Torres Vega",
        "username": "miguel_gasfitero_tambo",
        "trade_category": "Gasfitería",
        "district": "El Tambo",
        "years_experience": 6,
        "avg_rating": Decimal("4.60"),
        "bio": "Gasfitero con 6 años de experiencia en El Tambo. Especializado en instalación de termas, calentadores solares y sistemas de gas doméstico.",
        "job_title": "Instalador Sanitario y Gas",
        "email": "miguel.torres@demo.pe",
        "listings": [
            {
                "trade_category": "Gasfitería",
                "title": "Instalación de terma eléctrica y solar",
                "description": "Instalo termas eléctricas (Bosch, Sole, Rheem) y calentadores solares. Incluye tubería de agua caliente, válvulas de seguridad y conexión eléctrica. Garantía de instalación.",
                "enriched_keywords": ["terma eléctrica", "calentador solar", "agua caliente", "instalación terma", "válvula de seguridad"],
                "districts": ["El Tambo", "Huancayo"],
                "price_reference": Decimal("280.00"),
                "price_unit": "proyecto",
                "availability": "inmediata",
                "views_count": 33,
            },
        ],
    },

    # ── CARPINTERÍA ───────────────────────────────────────────────────────────
    {
        "full_name": "Roberto Espinoza Cárdenas",
        "username": "roberto_carpintero_hyo",
        "trade_category": "Carpintería",
        "district": "Huancayo",
        "years_experience": 15,
        "avg_rating": Decimal("4.90"),
        "bio": "Maestro carpintero con 15 años fabricando muebles de madera a medida en Huancayo. Trabajo en madera sólida, melanina y MDF. Diseños modernos y clásicos.",
        "job_title": "Maestro Carpintero",
        "email": "roberto.espinoza@demo.pe",
        "listings": [
            {
                "trade_category": "Carpintería",
                "title": "Closets y roperos de madera a medida",
                "description": "Fabricación e instalación de closets empotrados con diseño personalizado. Madera sólida, melanina o MDF según presupuesto. Incluye rieles corredizos, jalaores y organización interior.",
                "enriched_keywords": ["closet empotrado", "ropero a medida", "melanina", "MDF", "carpintería fina", "mueble a medida"],
                "districts": ["Huancayo", "El Tambo", "Chilca"],
                "price_reference": Decimal("550.00"),
                "price_unit": "proyecto",
                "availability": "semana",
                "views_count": 44,
            },
            {
                "trade_category": "Carpintería",
                "title": "Muebles de cocina integral en madera y melanina",
                "description": "Diseño y fabricación de cocinas integrales con alacenas, cajones y módulos inferiores. Tablero de granito o mármol opcional. Instalación incluida con garantía de acabados.",
                "enriched_keywords": ["cocina integral", "alacena", "módulo cocina", "tablero granito", "carpintería cocina"],
                "districts": ["Huancayo"],
                "price_reference": Decimal("1200.00"),
                "price_unit": "proyecto",
                "availability": "mes",
                "views_count": 29,
            },
        ],
    },
    {
        "full_name": "Alejandro Sánchez Meza",
        "username": "alejandro_carpintero_chilca",
        "trade_category": "Carpintería",
        "district": "Chilca",
        "years_experience": 9,
        "avg_rating": Decimal("4.55"),
        "bio": "Carpintero especializado en puertas, ventanas y estructuras de madera. Trabajo garantizado. Atiendo Chilca, Huancayo y alrededores.",
        "job_title": "Carpintero de Obra",
        "email": "alejandro.sanchez@demo.pe",
        "listings": [
            {
                "trade_category": "Carpintería",
                "title": "Instalación de puertas y ventanas de madera",
                "description": "Fabricación e instalación de puertas macizas, contraplacadas y ventanas de madera. Incluye marcos, bisagras, cerraduras y acabado en pintura o barniz.",
                "enriched_keywords": ["puerta de madera", "ventana de madera", "marco de puerta", "carpintería", "bisagra", "cerradura"],
                "districts": ["Chilca", "Huancayo"],
                "price_reference": Decimal("220.00"),
                "price_unit": "proyecto",
                "availability": "inmediata",
                "views_count": 21,
            },
        ],
    },

    # ── ALBAÑILERÍA ───────────────────────────────────────────────────────────
    {
        "full_name": "Francisco Mamani Condori",
        "username": "francisco_albanil_hyo",
        "trade_category": "Albañilería",
        "district": "Huancayo",
        "years_experience": 18,
        "avg_rating": Decimal("4.75"),
        "bio": "Maestro de obras con 18 años en construcción y remodelación en Huancayo. Especializado en muros de ladrillo, losas de concreto y acabados interiores y exteriores.",
        "job_title": "Maestro de Obras",
        "email": "francisco.mamani@demo.pe",
        "listings": [
            {
                "trade_category": "Albañilería",
                "title": "Construcción y remodelación de ambientes",
                "description": "Construcción de cuartos adicionales, muros perimetrales y remodelación integral de cocinas y baños. Trabajo con cemento, ladrillo King-Kong y fierro de construcción. Presupuesto detallado sin costo.",
                "enriched_keywords": ["construcción", "remodelación", "muro ladrillo", "losa concreto", "albañilería", "maestro de obras"],
                "districts": ["Huancayo", "El Tambo"],
                "price_reference": Decimal("60.00"),
                "price_unit": "dia",
                "availability": "semana",
                "views_count": 58,
            },
            {
                "trade_category": "Albañilería",
                "title": "Tarrajeo, enchape y acabados de interiores",
                "description": "Tarrajeo de paredes y techos con cemento fino. Enchape de cerámicos y porcelanatos en baños y cocinas. Colocación de cornisas y acabados decorativos. Trabajo prolijo y puntual.",
                "enriched_keywords": ["tarrajeo", "enchape cerámico", "porcelanato", "acabado interior", "enlucido", "cemento"],
                "districts": ["Huancayo", "El Tambo", "Chilca"],
                "price_reference": Decimal("55.00"),
                "price_unit": "dia",
                "availability": "inmediata",
                "views_count": 41,
            },
        ],
    },
    {
        "full_name": "Héctor Chávez Rojas",
        "username": "hector_albanil_tambo",
        "trade_category": "Albañilería",
        "district": "El Tambo",
        "years_experience": 11,
        "avg_rating": Decimal("4.45"),
        "bio": "Albañil con 11 años de experiencia en construcción civil. Trabajo en El Tambo y Huancayo. Especializado en construcción de muros y losas.",
        "job_title": "Albañil - Constructor Civil",
        "email": "hector.chavez@demo.pe",
        "listings": [
            {
                "trade_category": "Albañilería",
                "title": "Construcción de muro perimetral y cerco",
                "description": "Construcción de cercos perimétricos con ladrillo caravista o tarrajeado. Incluye excavación de cimientos, acero de refuerzo y acabado final. Presupuesto por metro lineal.",
                "enriched_keywords": ["cerco perimétrico", "muro ladrillo", "cimiento", "acero de refuerzo", "construcción"],
                "districts": ["El Tambo", "Huancayo"],
                "price_reference": Decimal("55.00"),
                "price_unit": "dia",
                "availability": "semana",
                "views_count": 19,
            },
        ],
    },

    # ── PINTURA ───────────────────────────────────────────────────────────────
    {
        "full_name": "Luis Alberto Medina Huanca",
        "username": "luis_pintor_hyo",
        "trade_category": "Pintura",
        "district": "Huancayo",
        "years_experience": 7,
        "avg_rating": Decimal("4.65"),
        "bio": "Pintor profesional con 7 años de experiencia en acabados interiores y exteriores. Uso pintura látex, esmalte y tráfico. Trabajo limpio con protección de muebles y pisos.",
        "job_title": "Pintor Decorativo",
        "email": "luis.medina@demo.pe",
        "listings": [
            {
                "trade_category": "Pintura",
                "title": "Pintura interior de departamento o casa",
                "description": "Pintura interior completa de ambientes: sala, dormitorios, cocina y servicios. Empaste previo, lijado y 2 manos de pintura látex Vencedor o similar. Incluye protección de pisos y muebles.",
                "enriched_keywords": ["pintura interior", "pintura látex", "empaste", "acabado pared", "pintor"],
                "districts": ["Huancayo", "El Tambo", "Chilca"],
                "price_reference": Decimal("5.00"),
                "price_unit": "hora",
                "availability": "inmediata",
                "views_count": 73,
            },
            {
                "trade_category": "Pintura",
                "title": "Pintura de fachada exterior y rejas",
                "description": "Pintura exterior con esmalte o pintura tráfico para fachadas, rejas metálicas y portones. Limpieza previa con arenado o lija. Base anticorrosiva para estructuras metálicas.",
                "enriched_keywords": ["pintura exterior", "fachada", "esmalte", "anticorrosivo", "reja metálica", "pintura tráfico"],
                "districts": ["Huancayo", "El Tambo"],
                "price_reference": Decimal("38.00"),
                "price_unit": "hora",
                "availability": "semana",
                "views_count": 26,
            },
        ],
    },

    # ── MECÁNICA AUTOMOTRIZ ───────────────────────────────────────────────────
    {
        "full_name": "Víctor Manuel Rojas Paredes",
        "username": "victor_mecanico_hyo",
        "trade_category": "Mecánica automotriz",
        "district": "Huancayo",
        "years_experience": 13,
        "avg_rating": Decimal("4.85"),
        "bio": "Técnico mecánico automotriz egresado del SENATI. 13 años reparando vehículos de todas las marcas. Diagnóstico computarizado. Taller propio en Huancayo.",
        "job_title": "Técnico Mecánico Automotriz",
        "email": "victor.rojas@demo.pe",
        "listings": [
            {
                "trade_category": "Mecánica automotriz",
                "title": "Mantenimiento preventivo y cambio de aceite",
                "description": "Mantenimiento completo: cambio de aceite y filtro, revisión de frenos, afinamiento de motor, cambio de bujías y revisión de suspensión. Aceite sintético o semi-sintético. Todas las marcas.",
                "enriched_keywords": ["mantenimiento automotriz", "cambio de aceite", "afinamiento motor", "frenos", "bujías", "suspensión"],
                "districts": ["Huancayo"],
                "price_reference": Decimal("120.00"),
                "price_unit": "proyecto",
                "availability": "inmediata",
                "views_count": 88,
            },
            {
                "trade_category": "Mecánica automotriz",
                "title": "Diagnóstico electrónico y reparación de motor",
                "description": "Diagnóstico computarizado con escáner OBD2. Reparación de fallas electrónicas, encendido, inyección de combustible y transmisión automática. Repuestos originales o alternativos garantizados.",
                "enriched_keywords": ["diagnóstico electrónico", "escáner OBD2", "inyección combustible", "transmisión automática", "reparación motor"],
                "districts": ["Huancayo"],
                "price_reference": Decimal("50.00"),
                "price_unit": "hora",
                "availability": "semana",
                "views_count": 45,
            },
        ],
    },

    # ── SOLDADURA ─────────────────────────────────────────────────────────────
    {
        "full_name": "César Augusto Tapia Luna",
        "username": "cesar_soldador_tambo",
        "trade_category": "Soldadura y metalurgia",
        "district": "El Tambo",
        "years_experience": 9,
        "avg_rating": Decimal("4.70"),
        "bio": "Fierrero y soldador con 9 años fabricando estructuras metálicas, rejas y portones en la región Junín. Soldadura eléctrica, MIG y autógena. Acabado con pintura anticorrosiva.",
        "job_title": "Soldador - Fierrero",
        "email": "cesar.tapia@demo.pe",
        "listings": [
            {
                "trade_category": "Soldadura y metalurgia",
                "title": "Fabricación e instalación de rejas y portones de fierro",
                "description": "Fabricación de rejas de seguridad, portones corredizos y batientes de fierro cuadrado y platinas. Diseños clásicos o modernos. Acabado con anticorrosivo y pintura al esmalte.",
                "enriched_keywords": ["reja de fierro", "portón corredizo", "soldadura", "estructura metálica", "anticorrosivo", "fierro cuadrado"],
                "districts": ["El Tambo", "Huancayo"],
                "price_reference": Decimal("380.00"),
                "price_unit": "proyecto",
                "availability": "semana",
                "views_count": 52,
            },
            {
                "trade_category": "Soldadura y metalurgia",
                "title": "Estructuras metálicas y escaleras de fierro",
                "description": "Fabricación de escaleras de fierro, barandas, cercos metálicos y estructuras para techos. Soldadura certificada MIG/MAG. Medidas a requerimiento del cliente.",
                "enriched_keywords": ["escalera metálica", "baranda fierro", "soldadura MIG", "estructura techo", "cerco metálico"],
                "districts": ["El Tambo", "Chilca"],
                "price_reference": Decimal("45.00"),
                "price_unit": "hora",
                "availability": "inmediata",
                "views_count": 34,
            },
        ],
    },
    {
        "full_name": "Pedro Huanca Sullca",
        "username": "pedro_soldador_chilca",
        "trade_category": "Soldadura y metalurgia",
        "district": "Chilca",
        "years_experience": 5,
        "avg_rating": Decimal("4.30"),
        "bio": "Soldador con 5 años de experiencia en metalmecánica. Especializado en acero inoxidable y trabajos de precisión para gastronomía e industria.",
        "job_title": "Soldador MIG/TIG",
        "email": "pedro.huanca@demo.pe",
        "listings": [
            {
                "trade_category": "Soldadura y metalurgia",
                "title": "Soldadura en acero inoxidable para cocinas industriales",
                "description": "Fabricación y reparación de mesones, estantes y estructuras en acero inoxidable para restaurantes, panaderías y cocinas industriales. Soldadura TIG de alta calidad. Acabado sanitario.",
                "enriched_keywords": ["acero inoxidable", "soldadura TIG", "meson inoxidable", "cocina industrial", "restaurante"],
                "districts": ["Chilca", "Huancayo"],
                "price_reference": Decimal("55.00"),
                "price_unit": "hora",
                "availability": "semana",
                "views_count": 17,
            },
        ],
    },

    # ── TECHADO ───────────────────────────────────────────────────────────────
    {
        "full_name": "Edilberto Paucar Ríos",
        "username": "edilberto_techero_hyo",
        "trade_category": "Techado",
        "district": "Huancayo",
        "years_experience": 14,
        "avg_rating": Decimal("4.80"),
        "bio": "Techero con 14 años instalando y reparando coberturas en Huancayo y toda la región Junín. Calamina, teja andina, PVC y eternit. Servicio de impermeabilización.",
        "job_title": "Techista Especializado",
        "email": "edilberto.paucar@demo.pe",
        "listings": [
            {
                "trade_category": "Techado",
                "title": "Instalación de techo de calamina y eternit",
                "description": "Instalación de coberturas con calamina galvanizada, eternit y teja PVC. Incluye estructura de madera o metalón, correas y acabado con sellador. Ideal para almacenes, casas y cobertizos.",
                "enriched_keywords": ["techo calamina", "eternit", "cobertura", "estructura madera", "techado", "correas"],
                "districts": ["Huancayo", "El Tambo", "Chilca"],
                "price_reference": Decimal("42.00"),
                "price_unit": "hora",
                "availability": "inmediata",
                "views_count": 61,
            },
            {
                "trade_category": "Techado",
                "title": "Impermeabilización de azotea y techos de concreto",
                "description": "Aplicación de impermeabilizante para techos de concreto con filtraciones. Sistema multicapa con malla geotextil y membrana asfáltica. Garantía de 5 años contra filtraciones.",
                "enriched_keywords": ["impermeabilización", "membrana asfáltica", "filtración techo", "azotea", "impermeabilizante"],
                "districts": ["Huancayo", "El Tambo"],
                "price_reference": Decimal("300.00"),
                "price_unit": "proyecto",
                "availability": "semana",
                "views_count": 49,
            },
        ],
    },
    {
        "full_name": "Segundo Castro Poma",
        "username": "segundo_techero_tambo",
        "trade_category": "Techado",
        "district": "El Tambo",
        "years_experience": 7,
        "avg_rating": Decimal("4.50"),
        "bio": "Techero con 7 años trabajando en El Tambo y alrededores. Especializado en teja andina y cobertura liviana para viviendas familiares.",
        "job_title": "Instalador de Coberturas",
        "email": "segundo.castro@demo.pe",
        "listings": [
            {
                "trade_category": "Techado",
                "title": "Instalación de techo con teja andina y PVC",
                "description": "Instalación de techo con teja andina de arcilla y PVC. Incluye cumbrera, limahoyas y sellado anti-goteo. Ideal para viviendas familiares que buscan estética y durabilidad.",
                "enriched_keywords": ["teja andina", "teja PVC", "cumbrera", "cobertura liviana", "techado vivienda"],
                "districts": ["El Tambo", "Chilca"],
                "price_reference": Decimal("320.00"),
                "price_unit": "proyecto",
                "availability": "inmediata",
                "views_count": 22,
            },
        ],
    },

    # ── JARDINERÍA ────────────────────────────────────────────────────────────
    {
        "full_name": "Nicanor Medrano Quispe",
        "username": "nicanor_jardinero_hyo",
        "trade_category": "Jardinería",
        "district": "Huancayo",
        "years_experience": 6,
        "avg_rating": Decimal("4.40"),
        "bio": "Jardinero con 6 años diseñando y manteniendo jardines en Huancayo. Poda, riego tecnificado, plantas ornamentales y grass natural y sintético.",
        "job_title": "Jardinero Paisajista",
        "email": "nicanor.medrano@demo.pe",
        "listings": [
            {
                "trade_category": "Jardinería",
                "title": "Diseño e instalación de jardín para casa",
                "description": "Diseño y creación de jardines interiores y exteriores. Instalación de grass natural o sintético, plantas ornamentales, sistema de riego por goteo y borde de piedra. Presupuesto sin costo.",
                "enriched_keywords": ["jardín", "grass natural", "grass sintético", "plantas ornamentales", "riego por goteo", "jardinería"],
                "districts": ["Huancayo"],
                "price_reference": Decimal("35.00"),
                "price_unit": "hora",
                "availability": "inmediata",
                "views_count": 38,
            },
        ],
    },

    # ── LIMPIEZA ──────────────────────────────────────────────────────────────
    {
        "full_name": "Rosa Elena Palomino Huanca",
        "username": "rosa_limpieza_hyo",
        "trade_category": "Limpieza y mantenimiento",
        "district": "Huancayo",
        "years_experience": 4,
        "avg_rating": Decimal("4.60"),
        "bio": "Trabajadora de limpieza con 4 años de experiencia en casas, oficinas y locales comerciales en Huancayo. Productos de calidad, discreta y puntual.",
        "job_title": "Técnica en Limpieza",
        "email": "rosa.palomino@demo.pe",
        "listings": [
            {
                "trade_category": "Limpieza y mantenimiento",
                "title": "Limpieza profunda de casa y departamento",
                "description": "Limpieza profunda de ambientes: desempolvado, limpieza de baños y cocina, lavado de ventanas, lustrado de pisos y desinfección. Incluye materiales de limpieza. Discreción garantizada.",
                "enriched_keywords": ["limpieza profunda", "limpieza hogar", "desinfección", "lustrado de pisos", "limpieza departamento"],
                "districts": ["Huancayo", "El Tambo"],
                "price_reference": Decimal("30.00"),
                "price_unit": "hora",
                "availability": "inmediata",
                "views_count": 94,
            },
        ],
    },
]

# ── USUARIOS TIPO PRIMER EMPLEO (para demo del flujo wizard) ──────────────────
PRIMER_EMPLEO_WORKERS = [
    {
        "full_name": "Ana Lucía García Pérez",
        "email": "ana.garcia@demo.pe",
        "district": "Huancayo",
    },
    {
        "full_name": "Kevin Alfredo Ríos Jara",
        "email": "kevin.rios@demo.pe",
        "district": "El Tambo",
    },
]

# ── USUARIOS TIPO EXPERIENCIA (para demo del flujo profesional) ───────────────
EXPERIENCIA_WORKERS = [
    {
        "full_name": "Patricia Isabel Vargas Lima",
        "email": "patricia.vargas@demo.pe",
        "district": "Huancayo",
        "job_title": "Asistente Contable",
        "years_experience": 5,
    },
    {
        "full_name": "Arturo Huamán Huayta",
        "email": "arturo.huaman@demo.pe",
        "district": "El Tambo",
        "job_title": "Técnico en Sistemas",
        "years_experience": 3,
    },
]

PASSWORD = "Demo2026!"


async def seed(session: AsyncSession) -> None:
    print("🌱 Iniciando seed demo — DRTPE-Junín (presentación Ministerio)...")

    # ── ADMIN ──────────────────────────────────────────────────────────────────
    admin = User(
        email="admin@drtpe-junin.gob.pe",
        hashed_password=hash_password("Admin2026!"),
        role="admin",
        is_active=True,
        email_verified=True,
    )
    session.add(admin)
    await session.flush()
    print(f"  ✓ Admin: {admin.email}")

    # ── TRABAJADORES DE OFICIO ─────────────────────────────────────────────────
    oficio_count = 0
    listing_count = 0

    for w_data in OFICIO_WORKERS:
        user = User(
            email=w_data["email"],
            hashed_password=hash_password(PASSWORD),
            role="worker",
            is_active=True,
            email_verified=True,
        )
        session.add(user)
        await session.flush()

        worker = Worker(
            id=str(uuid.uuid4()),
            user_id=user.id,
            worker_type="oficio",
            full_name=encrypt_field(w_data["full_name"]),
            dni=encrypt_field(f"{40000000 + oficio_count * 1337:08d}"),
            phone=encrypt_field(f"+519{61000000 + oficio_count * 997:08d}"),
            district=w_data["district"],
            trade_category=w_data["trade_category"],
            years_experience=w_data["years_experience"],
            avg_rating=w_data["avg_rating"],
            is_available=True,
            profile_completeness=90,
            bio=w_data["bio"],
            job_title=w_data["job_title"],
            username=w_data["username"],
        )
        session.add(worker)
        await session.flush()

        for l_data in w_data["listings"]:
            listing = ServiceListing(
                id=str(uuid.uuid4()),
                worker_id=worker.id,
                trade_category=l_data["trade_category"],
                title=l_data["title"],
                description=l_data["description"],
                enriched_keywords=l_data["enriched_keywords"],
                districts=l_data["districts"],
                price_reference=l_data["price_reference"],
                price_unit=l_data["price_unit"],
                availability=l_data["availability"],
                is_active=True,
                views_count=l_data["views_count"],
            )
            session.add(listing)
            listing_count += 1

        oficio_count += 1

    print(f"  ✓ {oficio_count} trabajadores de OFICIO creados")
    print(f"  ✓ {listing_count} publicaciones en el marketplace")

    # ── TRABAJADORES PRIMER EMPLEO ─────────────────────────────────────────────
    for i, p_data in enumerate(PRIMER_EMPLEO_WORKERS):
        user = User(
            email=p_data["email"],
            hashed_password=hash_password(PASSWORD),
            role="worker",
            is_active=True,
            email_verified=True,
        )
        session.add(user)
        await session.flush()

        worker = Worker(
            id=str(uuid.uuid4()),
            user_id=user.id,
            worker_type="primer_empleo",
            full_name=encrypt_field(p_data["full_name"]),
            dni=encrypt_field(f"{70000000 + i * 3721:08d}"),
            district=p_data["district"],
            is_available=True,
            profile_completeness=40,
        )
        session.add(worker)

    print(f"  ✓ {len(PRIMER_EMPLEO_WORKERS)} trabajadores PRIMER EMPLEO creados")

    # ── TRABAJADORES EXPERIENCIA ───────────────────────────────────────────────
    for i, e_data in enumerate(EXPERIENCIA_WORKERS):
        user = User(
            email=e_data["email"],
            hashed_password=hash_password(PASSWORD),
            role="worker",
            is_active=True,
            email_verified=True,
        )
        session.add(user)
        await session.flush()

        worker = Worker(
            id=str(uuid.uuid4()),
            user_id=user.id,
            worker_type="experiencia",
            full_name=encrypt_field(e_data["full_name"]),
            dni=encrypt_field(f"{80000000 + i * 2891:08d}"),
            district=e_data["district"],
            job_title=e_data.get("job_title"),
            years_experience=e_data.get("years_experience", 0),
            is_available=True,
            profile_completeness=60,
        )
        session.add(worker)

    print(f"  ✓ {len(EXPERIENCIA_WORKERS)} trabajadores EXPERIENCIA creados")

    await session.commit()

    print()
    print("✅ Seed demo completado exitosamente.")
    print(f"   👷 Oficio:        {oficio_count} trabajadores, {listing_count} servicios en marketplace")
    print(f"   🎓 Primer empleo: {len(PRIMER_EMPLEO_WORKERS)} trabajadores")
    print(f"   💼 Experiencia:   {len(EXPERIENCIA_WORKERS)} trabajadores")
    print()
    print("   Credenciales de prueba:")
    print("   ─────────────────────────────────────────────────────────")
    print("   Admin:         admin@drtpe-junin.gob.pe   / Admin2026!")
    print("   Electricista:  carlos.huaman@demo.pe       / Demo2026!")
    print("   Gasfitero:     juan.quispe@demo.pe         / Demo2026!")
    print("   Carpintero:    roberto.espinoza@demo.pe    / Demo2026!")
    print("   Mecánico:      victor.rojas@demo.pe        / Demo2026!")
    print("   Primer empleo: ana.garcia@demo.pe          / Demo2026!")
    print("   Experiencia:   patricia.vargas@demo.pe     / Demo2026!")
    print()
    print("   Portfolios públicos de ejemplo:")
    print("   /p/carlos_electricista_hyo")
    print("   /p/victor_mecanico_hyo")
    print("   /p/roberto_carpintero_hyo")
    print("   ─────────────────────────────────────────────────────────")


async def main() -> None:
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    session_local = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_local() as session:
        await seed(session)
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
