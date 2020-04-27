```
{%- for community in communities %} 
  ip community-list {{ community.description }} permit {{ community.value }}
{%- endfor %}
```