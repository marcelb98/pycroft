# -*- coding: utf-8 -*-
# Copyright (c) 2012 The Pycroft Authors. See the AUTHORS file.
# This file is part of the Pycroft project and licensed under the terms of
# the Apache License, Version 2.0. See the LICENSE file for details.
"""
    web.blueprints.properties
    ~~~~~~~~~~~~~~

    This module defines view functions for /properties

    :copyright: (c) 2012 by AG DSN.
"""

from flask import Blueprint, flash, redirect, render_template, url_for
from web.blueprints.navigation import BlueprintNavigation
from web.blueprints.properties.forms import PropertyGroupForm, TrafficGroupForm
from pycroft.model.properties import PropertyGroup, TrafficGroup, \
    Property, property_categories, get_properties
from pycroft.model.session import session

bp = Blueprint('properties', __name__, )
nav = BlueprintNavigation(bp, "Eigenschaften")


@bp.route('/traffic_groups')
@nav.navigate(u"Traffic Gruppen")
def traffic_groups():
    traffic_groups_list = TrafficGroup.q.all()
    return render_template('properties/traffic_groups_list.html',
        traffic_groups=traffic_groups_list)


@bp.route('/traffic_group/create', methods=['GET', 'POST'])
def traffic_group_create():
    form = TrafficGroupForm()
    if form.validate_on_submit():
        # traffic limit in byte per seven days
        new_traffic_group = TrafficGroup(name=form.name.data,
            traffic_limit=int(form.traffic_limit.data)*1024*1024*1024)
        session.add(new_traffic_group)
        session.commit()
        flash('Traffic Gruppe angelegt', 'success')
        return redirect(url_for('.traffic_groups'))
    return render_template('properties/traffic_group_create.html', form=form,
    page_title = u"Neue Traffic Gruppe")


@bp.route('/traffic_group/<group_id>/delete')
def traffic_group_delete(group_id):
    group = TrafficGroup.q.get(group_id)
    session.delete(group)
    session.commit()
    flash('Traffic Gruppe gelöscht', 'success')
    return redirect(url_for('.traffic_groups'))


@bp.route('/property_groups')
@nav.navigate(u"Eigenschaften Gruppen")
def property_groups():
    property_groups_list = PropertyGroup.q.all()
    return render_template('properties/property_groups_list.html',
        property_categories = property_categories,
        property_groups=property_groups_list,
        num_groups = len(property_groups_list))


@bp.route('/property_group/create', methods=['GET', 'POST'])
def property_group_create():
    form = PropertyGroupForm()
    if form.validate_on_submit():
        new_property_group = PropertyGroup(name=form.name.data)
        session.add(new_property_group)
        session.commit()
        flash('Eigenschaften Gruppe {} angelegt'.format(new_property_group.name), 'success')
        return redirect(url_for('.property_groups'))
    return render_template('properties/property_group_create.html', form=form,
        page_title = u"Neue Eigenschaften Gruppe")


@bp.route('/property_group/<group_id>/add/<property_name>')
def property_group_add_property(group_id, property_name):
    group = PropertyGroup.q.get(group_id)
    assert group
    assert(property_name in get_properties())
    new_property = Property(name=property_name, property_group_id=group_id)
    session.add(new_property)
    session.commit()
    flash('Eigenschaft {} zur Gruppe {} hinzugefügt'.format(property_name,
        group.name), 'success')
    return redirect(url_for('.property_groups'))


@bp.route('/property_group/<group_id>/delete/<property_name>')
def property_group_delete_property(group_id, property_name):
    group = PropertyGroup.q.get(group_id)
    assert group
    assert(property_name in get_properties())
    Property.q.filter_by(name=property_name,
        property_group_id = group_id).delete()
    session.commit()
    flash('Eigenschaft {} von Gruppe {} entfernt'.format(property_name,
        group.name), 'success')
    return redirect(url_for('.property_groups'))


@bp.route('/property_group/<group_id>/delete')
def property_group_delete(group_id):
    group = PropertyGroup.q.get(group_id)
    session.delete(group)
    session.commit()
    flash('Eigenschaften Gruppe {} gelöscht'.format(group.name), 'success')
    return redirect(url_for('.property_groups'))