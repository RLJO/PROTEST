/** @odoo-module **/

import publicWidget from "web.public.widget";
import "website_sale.website_sale";

publicWidget.registry.WebsiteSale.include({
    _onChangeCombination: function (ev, $parent, combination) {
        this._super(...arguments);
        console.log(combination)
        if (combination.wk_packaging) {

            $parent.find('.wk_packaging').replaceWith(combination.wk_packaging);
        }
    },
    /**
    * @override
    */
    _submitForm: function () {
        const params = this.rootProduct;

        const $product = $('#product_detail');
        const productTrackingInfo = $product.data('product-tracking-info');
        if (productTrackingInfo) {
            productTrackingInfo.quantity = params.quantity;
            $product.trigger('add_to_cart_event', [productTrackingInfo]);
        }
        // package_selector
        params.attrib = this.$form.find('.package_selector :selected').val();
        // 
        params.add_qty = params.quantity;
        params.product_custom_attribute_values = JSON.stringify(params.product_custom_attribute_values);
        params.no_variant_attribute_values = JSON.stringify(params.no_variant_attribute_values);
        return this.addToCart(params);
    },
})

// odoo.define('website_display_packaging_options.wk_productpackaging', function (require) {
//     "use strict";

//     var publicWidget = require('web.public.widget');
//     var VariantMixin = require('sale.VariantMixin');
//     const wUtils = require('website.utils');

//     publicWidget.registry.WebsiteSale.include({

//         /**
//          * Adds the stock checking to the regular _onChangeCombination method
//          * @override
//          */
//         _onChangeCombination: function (ev, $parent, combination) {
//             this._super(...arguments);
//             console.log(combination)
//             if (combination.wk_packaging) {

//                 $parent.find('.wk_packaging').replaceWith(combination.wk_packaging);
//             }
//             VariantMixin._onChangeCombination.apply(this, arguments);
//         },
//         /**
//         * @override
//         */
//         _submitForm: function () {
//             let params = this.rootProduct;
//             params.add_qty = params.quantity;
//             params.attrib = this.$form.find('.package_selector :selected').val();

//             params.product_custom_attribute_values = JSON.stringify(params.product_custom_attribute_values);
//             params.no_variant_attribute_values = JSON.stringify(params.no_variant_attribute_values);
            
//             if (this.isBuyNow) {
//                 params.express = true;
//             }
//             return wUtils.sendRequest('/shop/cart/update', params);
//         },
//     });

// });