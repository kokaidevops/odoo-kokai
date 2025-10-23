odoo.define('webclient_debugger.debug_menu', function (require) {
    "use strict";

    const { registry } = require('@web/core/registry');
    const { useService } = require("@web/core/utils/hooks");
    const { Component, hooks, useState, onMounted } = owl;

    class debugMenu extends Component{
        setup(){
            super.setup();
            this.router = useService("router");
            this.menus = useService("menu");
            this.state = useState({
                debug_mode: '',
                currentUrl: ''
            });
            this.onMounted(this.onMounted);
        }

        onMounted() {
            if(window.location.href.toString().includes('debug=1')){
                this.state.debug_mode = 'on';
            }else{
                this.state.debug_mode = 'off';
            }
        }


        toggleDebugMode(mode){
            if(mode == 'on'){
                this.state.debug_mode = 'off'
            }
            if(mode == 'off'){
                this.state.debug_mode = 'on'
            }
        }
    }
    debugMenu.template = 'webclient_debugger.debugMenu';

    registry.category("systray").add("debug_menu", { Component: debugMenu, }, { sequence: 2})

});