"""
Regenera assets/data.js de la Ficha de Giras de Prestaciones Sociales a partir de los Excel de origen.

Uso (desde la carpeta del proyecto):
    python herramientas/actualizar_datos.py --catalogos General_Catalogos.xlsx \
        --inscritos Claude_inscritos.xlsx --asistencias Asistencias.xlsx --plantilla Plantilla.xlsx

Requiere: pip install pandas openpyxl
Los datos que no vienen en Excel (PPI del APEF 2027, acervo cultural y mantenimiento)
se toman de la carpeta datos/ en formato JSON.
"""
import argparse, json, math, pathlib
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

    for k, f in (("ppi", "ppi_apef2027.json"), ("acervo", "acervo.json"), ("mantenimiento", "mantenimiento.json")):
        d[k] = json.loads((RAIZ / "datos" / f).read_text(encoding="utf-8"))

    salida = RAIZ / "assets" / "data.js"
    salida.write_text("/* Datos de la Ficha de Giras de Prestaciones Sociales. Generado con herramientas/actualizar_datos.py */\nwindow.FICHA_DATA = "
                      + json.dumps(d, ensure_ascii=False, separators=(",", ":")) + ";\n", encoding="utf-8")
    print("Listo:", salida, {k: len(v) for k, v in d.items()})


if __name__ == "__main__":
    main()
