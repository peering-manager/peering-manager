# Policies

Peering Manager allows _routing policies_ to be defined.
These policies can then be applied to:

* Autonomous Systems,
* Internet Exchanges and
    * Internet Exchange Peering Sessions,
* BGP Groups and
    * Direct Peering Sessions

First, these policies defined in Peering Manager must be exported via a template
to the router, then they need to be applied to prefixes received or announced.

For the template to process the policy, it must have a specific form in JSON.
Please find below an example for an export policy named "peering-rs-dus-out"
including statements for both Cisco IOS and Cisco IOS XR:

```JSON
{
	"cisco-ios": [{
			"match": ["community pm-announce-to-peers-ingress"],
			"result": "permit"
		},
		{
			"match": ["community pm-announce-to-all-ingress"],
			"result": "permit",
            "set": ["metric 0"]
		},
		{
			"match": ["community pm-announce-to-peers-customers-ingress"],
			"result": "permit"
		}
	],
	"cisco-iosxr": [
		"if large-community matches-any announce-to-dus-peers or destination in my-networks then",
		" set med 0",
		" pass",
		"else",
		" drop",
		"endif"
	]
}
```

Note that both policies have outside references, in IOS we need to have
_community-lists_ defined and in IOS XR we match for a _large-community-set_.

You can add more entries for more platforms as you like. As you see at the first
glance, there is no "one size fits all" - the policies need to defined for every
platform.

How they are transformed to a valid configuration is the job of the template.


!!! attention
    How policies are handled by templates shown here is pretty much
    work in progress.
    Ideas how your templates handle policies are very much welcome.

=== "Cisco IOS"
    We have to create _route-maps_, for this we merge all policies of a session
    (Peering Manager takes care of this) and then transform the entries into
    route-map clauses.

    ```no-highlight
    {%- for ixp in internet_exchange_points %}
      {%- for session in ixp |  sessions %}
        {%- if session.enabled %}
    ! Session with AS{{session.autonomous_system.asn}} ID:{{ session.id }} at {{ixp.name}}
    ! In: {{session | merge_import_policies |  iterate('slug') | join(',') }}
          {%-for policy in session | merge_import_policies%}
            {%-set outer=loop.index%}
            ! {{policy.slug}}
            {%- if policy.config_context is iterable %}
              {%- for part in policy.config_context %}
                {%- if part == template_type%}
                  {%- for statement in policy.config_context[part] %}
                  route-map {{p}}session-as{{session.autonomous_system.asn}}-id{{session.id}}-in {{statement.result}} {{outer*1000+loop.index}}
                    {%-for inner in statement.match%}
                    match {{inner}}
                    {%-endfor%}
                    {%-for inner in statement.set%}
                    set {{inner}}
                    {%-endfor%}
                  {%-endfor%}
                {%-endif%}
              {%-endfor%}
            {%-endif%}
          {%-endfor%}
          {%-for policy in session | merge_export_policies%}
            {%-set outer=loop.index%}
            ! {{policy.slug}}
            {%- if policy.config_context is iterable %}
              {%- for part in policy.config_context %}
                {%- if part == template_type%}
                  {%- for statement in policy.config_context[part] %}
                  route-map {{p}}session-as{{session.autonomous_system.asn}}-id{{session.id}}-out {{statement.result}} {{outer*1000+loop.index}}
                    {%-for inner in statement.match%}
                    match {{inner}}
                    {%-endfor%}
                    {%-for inner in statement.set%}
                    set {{inner}}
                    {%-endfor%}
                  {%-endfor%}
                {%-endif%}
              {%-endfor%}
            {%-endif%}
          {%-endfor%}
        {%-endif%}
      {%-endfor%}
    {%-endfor%}
    ```

    The result in this case is:
    ```
    ! Session with AS56890 ID:29 at DE-CIX Dusseldorf
    ! peering-rs-dus-out
    route-map pm-session-as56890-id29-out permit 1001
        match community pm-announce-to-peers-ingress
    route-map pm-session-as56890-id29-out permit 1002
        match community pm-announce-to-all-ingress
        set metric 0
    route-map pm-session-as56890-id29-out permit 1003
        match community pm-announce-to-peers-customers-ingress
    ```

    This looks complicated but just have a look how the statements of the policy
    are transformed:

    * The value of _result_ ends up as result of the route-map.
    * The values of _match_ are put into match statements. You can have multiple
    match statements.
    * The values of _set_ are put into set statements. You can have as many set
    statements as you like
    * The numbering of the route-map clauses is done automatically.

=== "Cisco IOS XR"
    In IOS XR we can generate all policies at once and call them later by name and also _apply_ policies within each other. That makes the template way shorter and less complicated.

    We dump simply the content of the policy into a _route-policy_ statement.

    ```
    {%- for policy in routing_policies %}
    !
    route-policy {{policy.name}}
    {%- if policy.config_context is iterable %}
      {%- for part in policy.config_context %}
        {%- if part == template_type%}
          {%- for statement in policy.config_context[part] %}
     {#- Simply dump all statements one after another#}
     {{statement}}
          {%-endfor%}
        {%-endif%}
      {%-endfor%}
    {%-endif%}
    end-policy
    {%-endfor%}
    ```

    Result for the same example as above is:
    ```
    route-policy peering-rs-dus-out
     if large-community matches-any announce-to-dus-peers or destination in my-networks then
      set med 0
      pass
     else
      drop
     endif
    end-policy
    ```
