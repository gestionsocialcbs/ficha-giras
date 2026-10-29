"""
Regenera assets/data.js de la Ficha de Giras de Prestaciones Sociales a partir de los Excel de origen.

Uso (desde la carpeta del proyecto):
    python herramientas/actualizar_datos.py --catalogos General_Catalogos.xlsx \
        --inscritos Claude_inscritos.xlsx --asistencias Asistencias.xlsx --plantilla Plantilla.xlsx \
        --patrimonio 2026_REGISTRO_REVISADO_DEL_PATRIMONIO_CULTURAL_IMSS.xlsx \
        --plantilla-unidades 1_Plantilla.xlsx

Requiere: pip install pandas openpyxl
Los datos que no vienen en Excel (PPI del APEF 2027 y mantenimiento)
se toman de la carpeta datos/ en formato JSON.
"""
import argparse, json, math, pathlib, re
import pandas as pd

RAIZ = pathlib.Path(__file__).resolve().parent.parent


def limpio(v):
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return None
    if hasattr(v, "item"):
        v = v.item()
    if isinstance(v, float) and v.is_integer():
        return int(v)
    if isinstance(v, str):
        return v.strip()
    return v


def filas(df):
    return [{k: limpio(v) for k, v in r.items()} for r in df.to_dict("records")]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--catalogos", required=True)
    ap.add_argument("--inscritos", required=True)
    ap.add_argument("--asistencias", required=True)
    ap.add_argument("--plantilla", required=True)
    ap.add_argument("--patrimonio", required=True, help="Registro revisado del Patrimonio Cultural IMSS")
    ap.add_argument("--plantilla-unidades", required=True, help="Plantilla de personal por unidad y puesto (1_Plantilla.xlsx)")
    ap.add_argument("--json-dir", help="Carpeta donde guardar además un JSON por tabla (para el tablero)")
    a = ap.parse_args()

    x = pd.read_excel(a.catalogos, sheet_name=None)
    d = {}
    d["cat_ooad"] = filas(x["OOAD"].rename(columns={"CVE_OOAD": "cve_ooad", "DES_OOAD": "ooad"}))
    r = x["Ranking"].iloc[:, :5].copy(); r.columns = ["cve_ooad", "periodo", "anio", "puntos", "ranking"]
    r["puntos"] = r["puntos"].round(2); d["ranking"] = filas(r)
    d["directorio"] = filas(x["Directorio"].rename(columns={"cv_deleg": "cve_ooad", "Titulo": "titulo", "Orden": "orden"})[["cve_ooad", "orden", "nombre", "cargo", "titulo", "siglas"]])
    d["mun_prioritarios"] = filas(x["Mun_prioritarios"].rename(columns={"CV_OOAD": "cve_ooad", "NOMGEO": "municipio"})[["cve_ooad", "municipio"]])
    d["gimnasios"] = filas(x["Cat_Gym"].rename(columns={"cantidad": "gimnasios", "Inscritos": "inscritos", "Asistencias": "asistencias"})[["cve_ooad", "gimnasios", "inscritos", "asistencias"]])
    d["acuaticas"] = filas(x["Instal_Acuáticas"].rename(columns={"cv_deleg": "cve_ooad", "cuenta": "cantidad"})[["cve_ooad", "tipo", "cantidad"]])
    d["top_actividades"] = filas(x["Top_Actividades"].rename(columns={"CVE_OOAD": "cve_ooad", "ACTIVIDAD_COMUN": "actividad", "INSCRITOS": "inscritos", "ASISTENCIAS": "asistencias", "TOP": "posicion"})[["cve_ooad", "posicion", "actividad", "inscritos", "asistencias"]])
    u = x["UOPSI"].copy()
    u["ciudad"] = u["Descripción-Ciudad"].astype(str).str.extract(r"Ciudad:\s*(.+)$")[0]
    u["instalaciones"] = u["Instalaciones"].apply(lambda s: "\n".join(l.strip() for l in str(s).splitlines() if l.strip()) if isinstance(s, str) else None)
    u = u.rename(columns={"Cv_OOAD": "cve_ooad", "Tipo": "tipo", "Clave": "clave", "Descripción": "unidad", "Aforo": "aforo", "Lat": "lat", "Long": "lon", "Funciones INBAL": "funciones_inbal", "Pvol": "personas_voluntarias", "Direccion": "direccion", "Estatus": "estatus", "Asis_IMSS_cultura": "asistencias_imss_cultura"})
    d["uopsi"] = filas(u[["cve", "cve_ooad", "tipo", "clave", "unidad", "ciudad", "lat", "lon", "aforo", "instalaciones", "funciones_inbal", "personas_voluntarias", "asistencias_imss_cultura", "direccion", "estatus"]])
    m = x["Mundialito_IMSS"].rename(columns={"Cv_OOAD": "cve_ooad", "Tipo": "tipo_unidad", "Descripción": "unidad", "Deporte": "modalidad", "Tipo_Instalación": "instalacion"})
    d["mundialito"] = filas(m[["cve", "cve_ooad", "unidad", "tipo_unidad", "modalidad", "instalacion"]])  # sin responsable ni contacto

    ins = pd.read_excel(a.inscritos)
    ins = ins.rename(columns={"CVE_OOAD": "cve_ooad", "DES_OOAD": "ooad",
        "RealInscritos_promocionsalud": "ps_ins_r", "ProgramadoInscritos_PromocionSalud": "ps_ins_p",
        "RealInscritos_Cultura": "dc_ins_r", "ProgramadoInscritos_Cultura": "dc_ins_p",
        "RealInscritos_Deportes": "cfd_ins_r", "ProgramadoInscritos_Deportes": "cfd_ins_p",
        "RealInscritos_Capacitacion": "cat_ins_r", "ProgramadoInscritos_Capacitacion": "cat_ins_p",
        "RealInscritos__total": "total_ins_r", "ProgramadoInscritos_total": "total_ins_p"})
    d["inscritos"] = filas(ins[["cve_ooad", "ooad", "ps_ins_r", "ps_ins_p", "dc_ins_r", "dc_ins_p", "cfd_ins_r", "cfd_ins_p", "cat_ins_r", "cat_ins_p", "total_ins_r", "total_ins_p"]])

    asi = pd.read_excel(a.asistencias).dropna(subset=["CVE_OOAD"]).copy()  # sin la fila de total nacional
    asi.columns = [c.lower() for c in asi.columns]
    for c in asi.columns:
        if c not in ("des_ooad", "des_uopsi"):
            asi[c] = asi[c].astype(int)
    d["asistencias"] = filas(asi.rename(columns={"des_ooad": "ooad", "des_uopsi": "uopsi"}))

    p = pd.read_excel(a.plantilla).rename(columns={"Plaza_autorizada": "plazas_autorizadas", "Plaza_cubierta": "plazas_cubiertas", "Plaza_vacante": "plazas_vacantes"})
    d["plantilla"] = filas(p[["cve_ooad", "plazas_autorizadas", "plazas_cubiertas", "plazas_vacantes"]])

    # Patrimonio cultural: encabezados en la fila 4 y datos desde la columna B
    pc = pd.read_excel(a.patrimonio, header=3).iloc[:, 1:].dropna(how="all")
    cve = {o["ooad"]: o["cve_ooad"] for o in d["cat_ooad"]}
    alias = {"DF Sur": "Sur del Distrito Federal", "DF Norte": "Norte del Distrito Federal",
             "Edoméx Poniente": "Estado de México Poniente", "Edoméx Oriente": "Estado de México Oriente"}
    acervo = []
    for _, r in pc.iterrows():
        o = str(r["OOAD"]).strip()
        tip = limpio(r["Tipología de obra"])
        acervo.append({"registro": limpio(r["Número de registro"]), "cve_ooad": cve.get(alias.get(o, o)), "ooad_registro": o,
                       "obra": limpio(r["Nombre de la obra"]), "autor": limpio(r["Autor"]), "inmueble": limpio(r["Inmueble IMSS"]),
                       "tecnica": limpio(r["Técnica"]), "fecha_realizacion": limpio(r["Fecha de realización"]),
                       "tipologia": tip if tip else "Sin tipología", "tipo_bien": limpio(r["Tipo de bien"]),
                       "clasificacion": limpio(r["Clasificación"])})  # Nivel Central queda sin cve_ooad
    d["acervo"] = acervo

    # Plantilla por unidad y puesto. Claves 35-36 = Norte del D.F. (39); 37-38 = Sur del D.F. (40)
    pu = pd.read_excel(a.plantilla_unidades, dtype={"NúmOOAD": str, "CveAdsc": str})
    nombres = json.loads((RAIZ / "datos" / "plantilla_nombres_unidad.json").read_text(encoding="utf-8"))
    def familia(p):
        p = " ".join(p.split())
        for k, v in (("PROF EDUC FISICA", "Profesores de educación física"), ("ORIENT EDUC FISICA", "Orientadores de educación física"),
                     ("ORIENT ACT FAMILIARES", "Orientadores de actividades familiares"), ("ORIENT INIC CULTURAL", "Orientadores de iniciación cultural"),
                     ("OR ACT ART", "Orientadores de actividades artísticas"), ("ORIENT ACT ART", "Orientadores de actividades artísticas"),
                     ("ORIENTADOR", "Orientadores"), ("PIANISTA", "Pianistas"), ("FIDEIMSS", "FIDEIMSS"), ("PERSONA VOLUNTARIA", "Personas voluntarias")):
            if p.startswith(k):
                return v
        if "ENTRENADOR" in p:
            return "Entrenadores"
        if "INST ENS" in p:
            return "Instructores de enseñanza"
        return "Otros puestos"
    filas_pl = []
    for i, r in pu.iterrows():
        k = int(r["NúmOOAD"]); k = {35: 39, 36: 39, 37: 40, 38: 40}.get(k, k)
        cve_u = r["CveAdsc"] if isinstance(r["CveAdsc"], str) and r["CveAdsc"].strip() else f"SC{k:02d}-{i + 1:03d}"
        nombre = nombres.get(cve_u) or " ".join(str(r["Adscripcion"]).split()).title()  # unidad nueva: revisar su nombre en datos/
        for c in pu.columns[4:]:
            n = int(r[c]) if not pd.isna(r[c]) else 0
            if n:
                raw = " ".join(c.split()); fam = familia(c); m = re.search(r"(\d+)$", raw)
                filas_pl.append({"cve_ooad": k, "cve_unidad": cve_u, "unidad": nombre, "puesto": raw, "familia": fam,
                                 "jornada": int(m.group(1)) if m and fam not in ("FIDEIMSS", "Personas voluntarias") else None, "cantidad": n})
    d["plantilla_puestos"] = filas_pl

    for k, f in (("ppi", "ppi_apef2027.json"), ("mantenimiento", "mantenimiento.json")):
        d[k] = json.loads((RAIZ / "datos" / f).read_text(encoding="utf-8"))

    if a.json_dir:
        out = pathlib.Path(a.json_dir); out.mkdir(parents=True, exist_ok=True)
        for k, v in d.items():
            (out / f"{k}.json").write_text(json.dumps(v, ensure_ascii=False, allow_nan=False), encoding="utf-8")

    # Validaciones básicas
    avisos = []
    for r in d["inscritos"]:
        if sum(r[f"{c}_ins_r"] for c in ("ps", "dc", "cfd", "cat")) != r["total_ins_r"]:
            avisos.append(f"Inscripciones: la suma de áreas no cuadra con el total en {r['ooad']}")
    sin_ooad = sorted({r["ooad_registro"] for r in d["acervo"] if r["cve_ooad"] is None} - {"Nivel Central"})
    if sin_ooad:
        avisos.append("Patrimonio: OOAD no reconocidas " + ", ".join(sin_ooad))
    nuevas = sorted({r["unidad"] for r in d["plantilla_puestos"] if r["cve_unidad"] not in nombres})
    if nuevas:
        avisos.append("Plantilla: unidades sin nombre oficial en datos/plantilla_nombres_unidad.json: " + ", ".join(nuevas))
    for a_ in avisos:
        print("AVISO:", a_)

    salida = RAIZ / "assets" / "data.js"
    salida.parent.mkdir(parents=True, exist_ok=True)
    salida.write_text("/* Datos de la Ficha de Giras de Prestaciones Sociales. Generado con herramientas/actualizar_datos.py */\nwindow.FICHA_DATA = "
                      + json.dumps(d, ensure_ascii=False, separators=(",", ":")) + ";\n", encoding="utf-8")
    print("Listo:", salida, {k: len(v) for k, v in d.items()})


if __name__ == "__main__":
    main()
