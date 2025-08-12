# How to Add Your Company Logo

## Option 1: Local File (Recommended)
1. Add your logo file (logo.png) to the project directory
2. Update line 194 in dashboard.py:
```python
st.image("logo.png", width=80)
```

## Option 2: URL
Replace the Meta logo URL on line 194 with your logo URL:
```python
st.image("https://your-company.com/logo.png", width=80)
```

## Option 3: Base64 Embedded
For maximum reliability, embed the logo:
```python
import base64

def get_logo_base64():
    with open("logo.png", "rb") as f:
        data = base64.b64encode(f.read()).decode()
    return f"data:image/png;base64,{data}"

# Then use:
st.markdown(f'<img src="{get_logo_base64()}" width="80">', unsafe_allow_html=True)
```

## Logo Requirements:
- Recommended size: 200x200px minimum
- Format: PNG with transparent background
- File size: Under 500KB