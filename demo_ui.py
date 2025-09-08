import streamlit as st
import subprocess
import threading
import time
import queue
import sys

# --- Page Configuration ---
st.set_page_config(layout="wide", page_title="Kafka Demo UI", page_icon="⚡")


# --- Session State Initialization ---
if 'services' not in st.session_state:
    st.session_state.services = {
        "orders": {"process": None, "log_queue": None, "logs": "", "icon": "📤"},
        "fulfillment": {"process": None, "log_queue": None, "logs": "", "icon": "⚙️"},
        "picklist": {"process": None, "log_queue": None, "logs": "", "icon": "📋"}
    }

# --- Backend Functions (No changes) ---

def enqueue_output(process, log_queue):
    try:
        for line in iter(process.stdout.readline, ''):
            log_queue.put(line)
        process.wait()
    finally:
        log_queue.put(None)

def start_script(name, script_name):
    service = st.session_state.services[name]
    if service["process"] is None:
        service["logs"] = f"🚀 Starting {name.capitalize()} service...\n"
        service["log_queue"] = queue.Queue()
        try:
            process = subprocess.Popen(
                [sys.executable, "-u", script_name],
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                encoding='utf-8', errors='replace'
            )
            service["process"] = process
            thread = threading.Thread(target=enqueue_output, args=(process, service["log_queue"]))
            thread.daemon = True
            thread.start()
            st.toast(f"{name.capitalize()} service started!", icon="✅")
        except FileNotFoundError:
            service["logs"] = f"❌ Error: Script '{script_name}' not found."
            service["process"] = None
            st.error(f"Script '{script_name}' not found!")
        except Exception as e:
            service["logs"] = f"❌ Error starting service: {str(e)}"
            service["process"] = None
            st.error(f"Failed to start {name.capitalize()}: {str(e)}")

def stop_script(name):
    service = st.session_state.services[name]
    process = service["process"]
    if process and process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
        service["logs"] += f"\n🛑 {name.capitalize()} service stopped by user\n"
        service["process"] = None
        st.toast(f"{name.capitalize()} stopped.", icon="🛑")

def clear_logs(name):
    st.session_state.services[name]["logs"] = ""
    st.toast(f"Logs for {name.capitalize()} cleared!")

def update_logs_from_queue():
    something_updated = False
    for name, service in st.session_state.services.items():
        if service["log_queue"]:
            while not service["log_queue"].empty():
                line = service["log_queue"].get_nowait()
                if line is None:
                    service["process"], service["log_queue"] = None, None
                    service["logs"] += f"\n✅ {name.capitalize()} process completed\n"
                    something_updated = True
                    break
                else:
                    service["logs"] += line
                    something_updated = True
    return something_updated

def create_service_control(name, script_name, show_status=True):
    service = st.session_state.services[name]
    is_running = service["process"] is not None and (service["process"].poll() is None)

    col1, col2 = st.columns([3, 1])
    with col1:
        st.header(f"{service['icon']} {name.capitalize()} Service")
    if show_status:
        with col2:
            if is_running:
                st.success("● Running")
            else:
                st.warning("● Stopped")

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("▶️ Start", key=f"start_{name}", use_container_width=True, disabled=is_running):
            start_script(name, script_name)
            st.rerun()
    with col2:
        if st.button("⏹️ Stop", key=f"stop_{name}", use_container_width=True, disabled=not is_running):
            stop_script(name)
            st.rerun()
    with col3:
        logs_exist = service["logs"].strip() != ""
        if st.button("🗑️ Clear Logs", key=f"clear_{name}", use_container_width=True, disabled=is_running or not logs_exist):
            clear_logs(name)
            st.rerun()

    st.subheader("📄 Service Logs")
    log_content = service["logs"] if service["logs"] else "No logs yet... Start the service to see output."
    st.code(log_content, language="bash")


# --- Main App Logic & UI Rendering ---
log_updated = update_logs_from_queue()

# --- Card 1: Main Header ---
with st.container(border=True):
    st.title("⚡ Kafka Demo")
    st.subheader("Manage your Orders, Fulfillment, and Picklist services")

# --- Card 2: Service Overview ---
with st.container(border=True):
    col1, col2, col3 = st.columns(3)
    services_to_display = ["orders", "fulfillment", "picklist"]
    for col, service_name in zip([col1, col2, col3], services_to_display):
        with col:
            service = st.session_state.services[service_name]
            st.markdown(f"### {service['icon']} {service_name.capitalize()}")
            is_running = service["process"] and service["process"].poll() is None
            if is_running:
                st.success("● Running")
            else:
                st.warning("● Stopped")

# --- Card 3: Service Controls and Logs ---
with st.container(border=True):
    tab_orders, tab_fulfillment, tab_picklist = st.tabs(["📤 Orders", "⚙️ Fulfillment", "📋 Picklist"])
    with tab_orders:
        create_service_control("orders", "order_producer.py", show_status=False)
    with tab_fulfillment:
        create_service_control("fulfillment", "fulfillment_service.py", show_status=False)
    with tab_picklist:
        create_service_control("picklist", "picklist_consumer.py", show_status=False)

# --- Auto-refresh loop ---
active_processes = any(s["process"] is not None and s["process"].poll() is None for s in st.session_state.services.values())
if active_processes or log_updated:
    time.sleep(0.5)
    st.rerun()