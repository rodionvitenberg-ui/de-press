# No support rays in the UI

Sending Silent Empathy as a separate "support rays" action is off in the browser. Support is Quiet Phrases (gestures) plus an optional Dialogue Request. Empathy Pulse / hearer rows stay on the server for existing data and Helper/outreach plumbing; they are not a visitor action. Notifications of kind `silent_empathy` are hidden from the inbox, like chat messages and Support Clouds.

We dropped rays because they duplicated the gesture clouds, created a public-feeling “I heard you” tap, and pulled Pulse/who-heard back into the product surface. ADR 0004 still forbids likes; the public signal is now the private cloud, not a ray button.
